package com.cycierge.admin

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.Cookie
import okhttp3.CookieJar
import okhttp3.HttpUrl
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

data class Room(
    val id: Int, val name: String, val tenantId: String,
    val since: String, val battery: Int, val unlockPending: Boolean
)
data class LogRow(val date: String, val time: String, val activity: String)
class AuthException : Exception("Session expired")

data class ReportBucket(val label: String, val unlocks: Int, val detections: Int, val occupiedDays: Int)
data class ReportRoom(
    val room: Int, val tenant: String, val checkins: Int,
    val unlocks: Int, val byTenant: Int, val byAdmin: Int, val detections: Int,
    val occupiedDays: Int, val occupancyPct: Double, val buckets: List<ReportBucket>
)
data class ReportTotals(
    val checkins: Int, val unlocks: Int, val byTenant: Int, val byAdmin: Int,
    val detections: Int, val occupiedDays: Int, val occupancyPct: Double
)
data class Report(
    val period: String, val start: String, val end: String, val days: Int, val elapsedDays: Int,
    val rooms: List<ReportRoom>, val totals: ReportTotals
)

object Api {
    private val json = "application/json".toMediaType()

    // PHPSESSID cookies, kept per host (LAN and Tailscale are different hosts).
    private val store = HashMap<String, List<Cookie>>()
    private val jar = object : CookieJar {
        override fun saveFromResponse(url: HttpUrl, cookies: List<Cookie>) = synchronized(store) {
            val old = store[url.host].orEmpty().filter { o -> cookies.none { it.name == o.name } }
            store[url.host] = old + cookies
        }
        override fun loadForRequest(url: HttpUrl): List<Cookie> = synchronized(store) { store[url.host].orEmpty() }
    }
    private val http = OkHttpClient.Builder().cookieJar(jar).callTimeout(6, TimeUnit.SECONDS).build()
    private val probe = http.newBuilder().callTimeout(2500, TimeUnit.MILLISECONDS).build()

    @Volatile private var base: String? = null
    @Volatile private var creds: Pair<String, String>? = null

    private fun reachable(root: String) = try {
        probe.newCall(Request.Builder().url("$root${Config.APP_PATH}/admin/api/ping.php").build())
            .execute().use { it.isSuccessful }
    } catch (e: IOException) { false }

    /** LAN first (2.5 s probe), then Tailscale. */
    suspend fun resolveBase(): String = withContext(Dispatchers.IO) {
        base ?: (listOf(Config.LAN, Config.TAILSCALE).firstOrNull { reachable(it) }
            ?: throw IOException("Pi unreachable (LAN and Tailscale)")).also { base = it }
    }

    suspend fun login(user: String, pass: String): Boolean = withContext(Dispatchers.IO) {
        val url = resolveBase() + Config.APP_PATH + "/admin/api/login.php"
        val body = JSONObject().put("username", user).put("password", pass).toString().toRequestBody(json)
        try {
            http.newCall(Request.Builder().url(url).post(body).build()).execute().use { r ->
                when (r.code) {
                    200 -> { creds = user to pass; true }
                    401 -> false
                    429 -> throw IOException("Too many failed attempts. Try again in 10 minutes.")
                    else -> throw IOException("Login failed: HTTP ${r.code}")
                }
            }
        } catch (e: IOException) { base = null; throw e }
    }

    fun logout() { creds = null; synchronized(store) { store.clear() } }

    private suspend fun call(path: String, body: JSONObject? = null, retry: Boolean = true): String =
        withContext(Dispatchers.IO) {
            val url = resolveBase() + Config.APP_PATH + path
            val req = Request.Builder().url(url).apply { if (body != null) post(body.toString().toRequestBody(json)) }.build()
            try {
                http.newCall(req).execute().use { r ->
                    if (r.code == 401) {
                        val c = creds
                        // New host (LAN <-> Tailscale) has no session yet: log in again once.
                        if (retry && c != null && login(c.first, c.second)) return@withContext call(path, body, false)
                        throw AuthException()
                    }
                    if (!r.isSuccessful) throw IOException("HTTP ${r.code} on $path")
                    r.body!!.string()
                }
            } catch (e: IOException) { base = null; throw e }
        }

    suspend fun rooms(): List<Room> {
        val a = JSONArray(call("/admin/api/status.php"))
        return (0 until a.length()).map {
            val o = a.getJSONObject(it)
            Room(
                id = o.optString("ID").toIntOrNull() ?: 0,
                name = o.optString("USERNAME"),
                tenantId = o.optString("USERID"),
                since = "${o.optString("USERDATE")} ${o.optString("USERTIME")}".trim(),
                battery = o.optString("USERBATT").toIntOrNull() ?: 0,
                unlockPending = o.optString("USERLOCK") == "1"
            )
        }
    }

    suspend fun unlock(room: Int) { call("/admin/api/unlock.php", JSONObject().put("room", room)) }

    suspend fun logs(room: Int): List<LogRow> {
        val a = JSONArray(call("/admin/api/logs.php?room=$room"))
        return (0 until a.length()).map {
            val o = a.getJSONObject(it)
            LogRow(o.optString("LOGSDATE"), o.optString("LOGSTIME"), o.optString("LOGSACTIVITY"))
        }
    }

    /** period = week | month | year; date = any yyyy-MM-dd inside the wanted period. */
    suspend fun report(period: String, date: String): Report {
        val o = JSONObject(call("/admin/api/report.php?period=$period&date=$date"))
        val ra = o.getJSONArray("rooms")
        val rooms = (0 until ra.length()).map { i ->
            val r = ra.getJSONObject(i)
            val ba = r.getJSONArray("buckets")
            ReportRoom(
                room = r.optInt("room"), tenant = r.optString("tenant"), checkins = r.optInt("checkins"),
                unlocks = r.optInt("unlocks"), byTenant = r.optInt("unlocks_tenant"), byAdmin = r.optInt("unlocks_admin"),
                detections = r.optInt("detections"), occupiedDays = r.optInt("occupied_days"),
                occupancyPct = r.optDouble("occupancy_pct", 0.0),
                buckets = (0 until ba.length()).map { j ->
                    val b = ba.getJSONObject(j)
                    ReportBucket(b.optString("label"), b.optInt("unlocks"), b.optInt("detections"), b.optInt("occupied_days"))
                }
            )
        }
        val t = o.getJSONObject("totals")
        return Report(
            period = o.optString("period"), start = o.optString("start"), end = o.optString("end"),
            days = o.optInt("days"), elapsedDays = o.optInt("elapsed_days"), rooms = rooms,
            totals = ReportTotals(
                t.optInt("checkins"), t.optInt("unlocks"), t.optInt("unlocks_tenant"), t.optInt("unlocks_admin"),
                t.optInt("detections"), t.optInt("occupied_days"), t.optDouble("occupancy_pct", 0.0)
            )
        )
    }

    /** Edit a tenant. Blank [password] keeps the current one (same rule as admin/Edit.php). */
    suspend fun updateUser(room: Int, name: String, userid: String, password: String) {
        call("/admin/api/update_user.php", JSONObject().put("room", room).put("name", name).put("userid", userid).put("password", password))
    }

    suspend fun clearLogs(room: Int) { call("/admin/api/clear_logs.php", JSONObject().put("room", room)) }

    /** One JPEG from cam.php (admin session cookie is sent automatically). Null if camera is down. */
    suspend fun snapshot(room: Int): Bitmap? = withContext(Dispatchers.IO) {
        try {
            val url = resolveBase() + Config.APP_PATH + "/cam.php?room=$room&who=admin"
            http.newCall(Request.Builder().url(url).build()).execute().use { r ->
                if (r.isSuccessful) BitmapFactory.decodeStream(r.body!!.byteStream()) else null
            }
        } catch (e: IOException) { null }
    }
}
