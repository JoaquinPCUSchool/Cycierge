package com.cycierge.admin

import android.net.ConnectivityManager
import android.net.Network
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.sp
import androidx.core.view.WindowCompat
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    // Wi-Fi <-> mobile data (or a different Wi-Fi): forget the cached route so it is re-probed.
    private val netCb = object : ConnectivityManager.NetworkCallback() {
        override fun onAvailable(network: Network) { Api.invalidate() }
        override fun onLost(network: Network) { Api.invalidate() }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        getSystemService(ConnectivityManager::class.java).registerDefaultNetworkCallback(netCb)
        window.statusBarColor = Cy.Navy.toArgb()
        window.navigationBarColor = Cy.Navy.toArgb()
        WindowCompat.getInsetsController(window, window.decorView).apply {
            isAppearanceLightStatusBars = false
            isAppearanceLightNavigationBars = false
        }
        setContent {
            CyTheme {
                Surface(Modifier.fillMaxSize().cyBackground(), color = Color.Transparent, contentColor = Cy.Cream) { App() }
            }
        }
    }

    override fun onDestroy() {
        getSystemService(ConnectivityManager::class.java).unregisterNetworkCallback(netCb)
        super.onDestroy()
    }
}

@Composable
fun App() {
    var loggedIn by remember { mutableStateOf(false) }
    var room by remember { mutableStateOf<Room?>(null) }
    var reports by remember { mutableStateOf(false) }
    var account by remember { mutableStateOf(false) }
    var edit by remember { mutableStateOf<Room?>(null) }
    var newT by remember { mutableStateOf<Room?>(null) }
    BackHandler(enabled = newT != null || edit != null || room != null || reports || account) {
        when {
            newT != null -> newT = null
            edit != null -> edit = null
            account -> account = false
            reports -> reports = false
            else -> room = null
        }
    }
    val r = room
    val e = edit
    val n = newT
    val logout = { Api.logout(); newT = null; edit = null; room = null; reports = false; account = false; loggedIn = false }
    when {
        !loggedIn -> LoginScreen { loggedIn = true }
        n != null -> NewTenantScreen(n, onBack = { newT = null }, onLogout = logout)
        e != null -> EditTenantScreen(e, onBack = { edit = null }, onLogout = logout)
        account -> AccountScreen(onBack = { account = false }, onLogout = logout)
        reports -> ReportScreen(onBack = { reports = false }, onLogout = logout)
        r == null -> DashboardScreen(onOpen = { room = it }, onEdit = { edit = it }, onNew = { newT = it }, onReports = { reports = true }, onAccount = { account = true }, onLogout = logout)
        else -> RoomScreen(r, onBack = { room = null }, onEdit = { edit = it }, onNew = { newT = it }, onLogout = logout)
    }
}

// ---------------------------------------------------------------- refresh
/**
 * Backs the refresh button. [trigger] reconnects to the Pi right now (see Api.reconnect) and bumps [key];
 * screens use [key] as a LaunchedEffect key, so their polling loops restart and reload immediately
 * instead of waiting out the 4-5 s delay.
 */
@Stable
internal class RefreshState(private val scope: CoroutineScope) {
    var key by mutableStateOf(0); private set
    var busy by mutableStateOf(false); private set

    fun trigger() {
        if (busy) return
        scope.launch {
            busy = true
            val t0 = System.currentTimeMillis()
            Api.reconnect()
            key++
            val left = 450 - (System.currentTimeMillis() - t0)   // keep the spinner visible on a fast LAN
            if (left > 0) delay(left)
            busy = false
        }
    }
}

@Composable
internal fun rememberRefresh(): RefreshState {
    val scope = rememberCoroutineScope()
    return remember { RefreshState(scope) }
}

// ---------------------------------------------------------------- login
@Composable
private fun FieldLabel(text: String) {
    Text(text, color = Cy.Mute, fontSize = 13.sp, fontWeight = FontWeight.SemiBold,
        modifier = Modifier.fillMaxWidth().padding(top = 10.dp, bottom = 4.dp))
}

@Composable
private fun cyFieldColors() = OutlinedTextFieldDefaults.colors(
    focusedContainerColor = Cy.Cream, unfocusedContainerColor = Cy.Cream,
    focusedTextColor = Cy.Navy, unfocusedTextColor = Cy.Navy,
    focusedBorderColor = Cy.Amber, unfocusedBorderColor = Color.Transparent,
    cursorColor = Cy.Navy
)

@Composable
fun LoginScreen(onOk: () -> Unit) {
    var user by remember { mutableStateOf("") }
    var pass by remember { mutableStateOf("") }
    var err by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val refresh = rememberRefresh()

    // Probe in the background while the login form is showing; cheap when the route is already cached.
    LaunchedEffect(Unit) { while (true) { runCatching { Api.resolveBase() }; delay(5000) } }

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 28.dp, vertical = 32.dp),
        verticalArrangement = Arrangement.Center, horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Wordmark(56.sp)
        Text("SECURITY MADE SMART", color = Cy.Mute, fontSize = 12.sp, letterSpacing = 2.5.sp, modifier = Modifier.padding(top = 6.dp))
        Row(Modifier.padding(top = 14.dp, bottom = 36.dp)) {
            Box(Modifier.width(98.dp).height(4.dp).clip(RoundedCornerShape(2.dp)).background(Cy.Amber))
            Box(Modifier.width(42.dp).height(4.dp).clip(RoundedCornerShape(2.dp)).background(Cy.Violet))
        }
        Text("Admin Login", fontSize = 18.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(8.dp))
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            RouteChip()
            RefreshButton(refresh.busy) { refresh.trigger() }
        }

        FieldLabel("Username")
        OutlinedTextField(user, { user = it }, singleLine = true, shape = RoundedCornerShape(12.dp),
            colors = cyFieldColors(), modifier = Modifier.fillMaxWidth())
        FieldLabel("Password")
        OutlinedTextField(pass, { pass = it }, singleLine = true, shape = RoundedCornerShape(12.dp),
            colors = cyFieldColors(), visualTransformation = PasswordVisualTransformation(),
            modifier = Modifier.fillMaxWidth())

        Spacer(Modifier.height(18.dp))
        err?.let { ErrorBox(it) }
        ActionButton(
            if (busy) "Signing in…" else "Log in",
            enabled = !busy && user.isNotBlank() && pass.isNotEmpty(),
            onClick = {
                busy = true; err = null
                scope.launch {
                    try {
                        if (Api.login(user.trim(), pass)) onOk() else err = "Wrong username or password"
                    } catch (e: Exception) { err = e.message ?: "Can't reach the Pi" }
                    busy = false
                }
            }
        )
    }
}

// ---------------------------------------------------------------- edit tenant
@Composable
fun EditTenantScreen(room: Room, onBack: () -> Unit, onLogout: () -> Unit) {
    var name by remember { mutableStateOf(room.name) }
    var uid by remember { mutableStateOf(room.tenantId) }
    var pass by remember { mutableStateOf("") }
    var err by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    Column(Modifier.fillMaxSize()) {
        CyTopBar(start = { RoundIcon(Ic.Back, "Back", onBack); Wordmark(20.sp) })
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(18.dp)) {
            Hero("Room no. ${room.id}", "Edit", "tenant")

            FieldLabel("Name of tenant")
            OutlinedTextField(name, { name = it }, singleLine = true, shape = RoundedCornerShape(12.dp),
                colors = cyFieldColors(), modifier = Modifier.fillMaxWidth())
            FieldLabel("Username (tenant login)")
            OutlinedTextField(uid, { uid = it }, singleLine = true, shape = RoundedCornerShape(12.dp),
                colors = cyFieldColors(), modifier = Modifier.fillMaxWidth())
            FieldLabel("New password")
            OutlinedTextField(pass, { pass = it }, singleLine = true, shape = RoundedCornerShape(12.dp),
                colors = cyFieldColors(), visualTransformation = PasswordVisualTransformation(),
                modifier = Modifier.fillMaxWidth())
            Text("Leave the password blank to keep the current one.", color = Cy.Mute, fontSize = 12.sp,
                modifier = Modifier.padding(top = 6.dp))

            Spacer(Modifier.height(20.dp))
            err?.let { ErrorBox(it) }
            ActionButton(
                if (busy) "Saving…" else "Save", icon = Ic.Lock,
                enabled = !busy && name.isNotBlank() && uid.isNotBlank(),
                onClick = {
                    busy = true; err = null
                    scope.launch {
                        try { Api.updateUser(room.id, name.trim(), uid.trim(), pass); onBack() }
                        catch (e: AuthException) { onLogout() }
                        catch (e: Exception) { err = e.message ?: "Couldn't save" }
                        busy = false
                    }
                }
            )
            Spacer(Modifier.height(10.dp))
            ActionButton("Cancel", onClick = onBack, style = Btn.Ghost)
            BrandFoot()
        }
    }
}

// ---------------------------------------------------------------- change admin login
private fun accountError(e: ApiError): String = when (e.key) {
    "wrong_password" -> "Current password is wrong."
    "blocked" -> "Too many failed attempts. Try again in 10 minutes."
    "bad_username" -> "Username must be 3-32 characters: letters, numbers, dot, dash or underscore."
    "weak_password" -> "New password must be at least 8 characters."
    "password_too_long" -> "New password is too long (72 characters max)."
    "same_password" -> "New password must be different from the current one."
    "nothing_to_change" -> "Nothing to change."
    else -> e.message ?: "Couldn't save"
}

@Composable
fun AccountScreen(onBack: () -> Unit, onLogout: () -> Unit) {
    val ctx = LocalContext.current
    val oldUser = remember { Api.currentUser() }
    var cur by remember { mutableStateOf("") }
    var newUser by remember { mutableStateOf(oldUser) }
    var newPass by remember { mutableStateOf("") }
    var again by remember { mutableStateOf("") }
    var err by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    val userOk = Regex("[A-Za-z0-9_.-]{3,32}").matches(newUser.trim())
    val passLenOk = newPass.isEmpty() || newPass.length >= 8
    val passMatch = newPass == again
    val changed = newUser.trim() != oldUser || newPass.isNotEmpty()
    val canSave = !busy && cur.isNotEmpty() && userOk && passLenOk && passMatch && changed

    Column(Modifier.fillMaxSize()) {
        CyTopBar(start = { RoundIcon(Ic.Back, "Back", onBack); Wordmark(20.sp) })
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(18.dp)) {
            Hero("Security", "Admin", "login")

            FieldLabel("Current password")
            OutlinedTextField(cur, { cur = it }, singleLine = true, shape = RoundedCornerShape(12.dp),
                colors = cyFieldColors(), visualTransformation = PasswordVisualTransformation(),
                modifier = Modifier.fillMaxWidth())

            FieldLabel("Username")
            OutlinedTextField(newUser, { newUser = it }, singleLine = true, shape = RoundedCornerShape(12.dp),
                colors = cyFieldColors(), modifier = Modifier.fillMaxWidth())
            if (!userOk) Text("3-32 characters: letters, numbers, . _ -", color = Cy.Low, fontSize = 12.sp,
                modifier = Modifier.padding(top = 6.dp))

            FieldLabel("New password")
            OutlinedTextField(newPass, { newPass = it }, singleLine = true, shape = RoundedCornerShape(12.dp),
                colors = cyFieldColors(), visualTransformation = PasswordVisualTransformation(),
                modifier = Modifier.fillMaxWidth())
            if (!passLenOk) Text("At least 8 characters.", color = Cy.Low, fontSize = 12.sp,
                modifier = Modifier.padding(top = 6.dp))
            else Text("Leave blank to keep the current password.", color = Cy.Mute, fontSize = 12.sp,
                modifier = Modifier.padding(top = 6.dp))

            FieldLabel("Confirm new password")
            OutlinedTextField(again, { again = it }, singleLine = true, shape = RoundedCornerShape(12.dp),
                colors = cyFieldColors(), visualTransformation = PasswordVisualTransformation(),
                modifier = Modifier.fillMaxWidth())
            if (!passMatch) Text("Passwords don't match.", color = Cy.Low, fontSize = 12.sp,
                modifier = Modifier.padding(top = 6.dp))

            Text("This also changes the web admin login. Other phones and browsers signed in as admin will be signed out.",
                color = Cy.Mute, fontSize = 12.sp, modifier = Modifier.padding(top = 14.dp))

            Spacer(Modifier.height(20.dp))
            err?.let { ErrorBox(it) }
            ActionButton(
                if (busy) "Saving…" else "Save", icon = Ic.Shield, enabled = canSave,
                onClick = {
                    busy = true; err = null
                    scope.launch {
                        try {
                            Api.changeCredentials(cur, newUser.trim(), newPass)
                            Toast.makeText(ctx, "Admin login updated", Toast.LENGTH_LONG).show()
                            onBack()
                        }
                        catch (e: AuthException) { onLogout() }
                        catch (e: ApiError) { err = accountError(e) }
                        catch (e: Exception) { err = e.message ?: "Couldn't save" }
                        busy = false
                    }
                }
            )
            Spacer(Modifier.height(10.dp))
            ActionButton("Cancel", onClick = onBack, style = Btn.Ghost)
            BrandFoot()
        }
    }
}

// ---------------------------------------------------------------- new tenant (check-in)
@Composable
fun NewTenantScreen(room: Room, onBack: () -> Unit, onLogout: () -> Unit) {
    var name by remember { mutableStateOf("") }
    var uid by remember { mutableStateOf("") }
    var pass by remember { mutableStateOf("") }
    var err by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    var confirm by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    val doSave: () -> Unit = {
        busy = true; err = null
        scope.launch {
            try { Api.newTenant(room.id, name.trim(), uid.trim(), pass); onBack() }
            catch (e: AuthException) { onLogout() }
            catch (e: Exception) { err = e.message ?: "Couldn't save" }
            busy = false
        }
    }

    Column(Modifier.fillMaxSize()) {
        CyTopBar(start = { RoundIcon(Ic.Back, "Back", onBack); Wordmark(20.sp) })
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(18.dp)) {
            Hero("Room no. ${room.id}", "New", "tenant")

            FieldLabel("Name of tenant")
            OutlinedTextField(name, { name = it }, singleLine = true, shape = RoundedCornerShape(12.dp),
                colors = cyFieldColors(), modifier = Modifier.fillMaxWidth())
            FieldLabel("Username (tenant login)")
            OutlinedTextField(uid, { uid = it }, singleLine = true, shape = RoundedCornerShape(12.dp),
                colors = cyFieldColors(), modifier = Modifier.fillMaxWidth())
            FieldLabel("Password")
            OutlinedTextField(pass, { pass = it }, singleLine = true, shape = RoundedCornerShape(12.dp),
                colors = cyFieldColors(), visualTransformation = PasswordVisualTransformation(),
                modifier = Modifier.fillMaxWidth())
            Text("Check-in time is set to now and time stayed restarts at 0.", color = Cy.Mute, fontSize = 12.sp,
                modifier = Modifier.padding(top = 6.dp))

            Spacer(Modifier.height(20.dp))
            err?.let { ErrorBox(it) }
            ActionButton(
                if (busy) "Saving…" else "Check in tenant", icon = Ic.Person,
                enabled = !busy && name.isNotBlank() && uid.isNotBlank() && pass.isNotEmpty(),
                onClick = { if (room.name.isBlank()) doSave() else confirm = true }
            )
            Spacer(Modifier.height(10.dp))
            ActionButton("Cancel", onClick = onBack, style = Btn.Ghost)
            BrandFoot()
        }
    }

    if (confirm) {
        AlertDialog(
            onDismissRequest = { confirm = false },
            containerColor = Cy.Navy2, titleContentColor = Cy.Cream, textContentColor = Cy.Mute,
            title = { Text("Replace ${room.name}?", fontWeight = FontWeight.ExtraBold) },
            text = { Text("Their stay in Room ${room.id} ends now and time stayed restarts for the new tenant.") },
            confirmButton = {
                TextButton(onClick = { confirm = false; doSave() }) {
                    Text("Check in", color = Cy.Amber, fontWeight = FontWeight.ExtraBold)
                }
            },
            dismissButton = { TextButton(onClick = { confirm = false }) { Text("Cancel", color = Cy.Mute) } }
        )
    }
}

// ---------------------------------------------------------------- building dashboard
@Composable
private fun RoomCard(r: Room, tick: Int, onUnlock: () -> Unit, onOpen: () -> Unit, onEdit: () -> Unit, onNew: () -> Unit) {
    val vacant = r.name.isBlank()
    val stay = if (vacant) null else stayText(r.since, tick)
    CyCard(border = if (r.unlockPending) Cy.Amber else Cy.Line) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Text(
                buildAnnotatedString {
                    append("Room no. ")
                    withStyle(SpanStyle(color = Cy.Amber)) { append(r.id.toString()) }
                },
                fontSize = 24.sp, fontWeight = FontWeight.ExtraBold
            )
            BatteryChip(r.battery)
        }
        Spacer(Modifier.height(12.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Row(Modifier.weight(1f), verticalAlignment = Alignment.CenterVertically) {
                IconTile(Ic.Person, 38.dp, round = true)
                Spacer(Modifier.width(10.dp))
                Column {
                    Text(if (vacant) "Status" else "Tenant", color = Cy.Mute, fontSize = 12.sp)
                    Text(if (vacant) "Unoccupied" else r.name, fontWeight = FontWeight.Bold, fontSize = 17.sp)
                }
            }
            if (stay != null) {
                Column(horizontalAlignment = Alignment.End) {
                    Text("Time stayed", color = Cy.Mute, fontSize = 12.sp)
                    Text(stay.first, color = Cy.Amber, fontSize = 24.sp, fontWeight = FontWeight.ExtraBold)
                    Text(stay.second, color = Cy.Mute, fontSize = 12.sp)
                }
            }
        }
        Spacer(Modifier.height(14.dp))
        ActionButton(
            if (r.unlockPending) "Unlocking…" else "Unlock door", onClick = onUnlock,
            icon = Ic.Unlock, enabled = !r.unlockPending, big = true
        )
        Spacer(Modifier.height(10.dp))
        ActionButton("Camera & logs", onClick = onOpen, icon = Ic.Camera, style = Btn.Teal)
        Spacer(Modifier.height(10.dp))
        ActionButton("Edit tenant", onClick = onEdit, icon = Ic.Person, style = Btn.Ghost)
        Spacer(Modifier.height(10.dp))
        ActionButton("New tenant", onClick = onNew, icon = Ic.Person, style = Btn.Ghost)
    }
}

@Composable
fun DashboardScreen(onOpen: (Room) -> Unit, onEdit: (Room) -> Unit, onNew: (Room) -> Unit, onReports: () -> Unit, onAccount: () -> Unit, onLogout: () -> Unit) {
    var rooms by remember { mutableStateOf<List<Room>>(emptyList()) }
    var err by remember { mutableStateOf<String?>(null) }
    var confirm by remember { mutableStateOf<Room?>(null) }
    var tick by remember { mutableStateOf(0) }
    val scope = rememberCoroutineScope()
    val refresh = rememberRefresh()

    LaunchedEffect(refresh.key) {
        while (true) {
            try { rooms = Api.rooms(); err = null }
            catch (e: CancellationException) { throw e }
            catch (e: AuthException) { onLogout(); return@LaunchedEffect }
            catch (e: Exception) { err = e.message ?: "Error" }
            tick++
            delay(4000)
        }
    }

    Column(Modifier.fillMaxSize()) {
        CyTopBar(
            start = { Wordmark(20.sp) },
            end = { RouteChip(); RefreshButton(refresh.busy) { refresh.trigger() }; RoundIcon(Ic.Logout, "Log out", onLogout) }
        )
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(18.dp)) {
            Hero("Admin management", "All", "rooms")
            err?.let { ErrorBox(it) }
            rooms.forEach { r ->
                RoomCard(r, tick, onUnlock = { confirm = r }, onOpen = { onOpen(r) }, onEdit = { onEdit(r) }, onNew = { onNew(r) })
                Spacer(Modifier.height(14.dp))
            }
            CyCard(onClick = onReports) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconTile(Ic.Chart)
                    Spacer(Modifier.width(14.dp))
                    Column(Modifier.weight(1f)) {
                        Text("Reports", fontWeight = FontWeight.ExtraBold, fontSize = 17.sp)
                        Text("Occupancy, unlocks & detections", color = Cy.Mute, fontSize = 13.sp)
                    }
                    CyIcon(Ic.Next, tint = Cy.Mute)
                }
            }
            Spacer(Modifier.height(14.dp))
            CyCard(onClick = onAccount) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconTile(Ic.Shield)
                    Spacer(Modifier.width(14.dp))
                    Column(Modifier.weight(1f)) {
                        Text("Admin login", fontWeight = FontWeight.ExtraBold, fontSize = 17.sp)
                        Text("Change username or password", color = Cy.Mute, fontSize = 13.sp)
                    }
                    CyIcon(Ic.Next, tint = Cy.Mute)
                }
            }
            BrandFoot()
        }
    }

    confirm?.let { r ->
        AlertDialog(
            onDismissRequest = { confirm = null },
            containerColor = Cy.Navy2, titleContentColor = Cy.Cream, textContentColor = Cy.Mute,
            title = { Text("Unlock Room ${r.id}?", fontWeight = FontWeight.ExtraBold) },
            confirmButton = {
                TextButton(onClick = {
                    confirm = null
                    scope.launch {
                        try { Api.unlock(r.id); rooms = Api.rooms() }
                        catch (e: AuthException) { onLogout() }
                        catch (e: Exception) { err = e.message }
                    }
                }) { Text("Unlock", color = Cy.Amber, fontWeight = FontWeight.ExtraBold) }
            },
            dismissButton = { TextButton(onClick = { confirm = null }) { Text("Cancel", color = Cy.Mute) } }
        )
    }
}

// ---------------------------------------------------------------- room: camera + unlock + logs
@Composable
private fun LogItem(l: LogRow) {
    val (label, kind) = friendlyActivity(l.activity)
    CyCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            when (kind) {
                2 -> IconTile(Ic.Shield, tint = Color(0xFFC9B8FF), bg = Color(0x594A1FB8))
                1 -> IconTile(Ic.Unlock)
                else -> IconTile(Ic.Book)
            }
            Spacer(Modifier.width(12.dp))
            Column {
                Text(label, fontWeight = FontWeight.Bold, fontSize = 15.sp)
                Text(whenText(l.date, l.time), color = Cy.Mute, fontSize = 12.sp)
            }
        }
    }
}

@Composable
fun RoomScreen(room: Room, onBack: () -> Unit, onEdit: (Room) -> Unit, onNew: (Room) -> Unit, onLogout: () -> Unit) {
    var cur by remember { mutableStateOf(room) }          // live copy: battery + unlock state
    var frame by remember { mutableStateOf<android.graphics.Bitmap?>(null) }
    var camDown by remember { mutableStateOf(false) }
    var logs by remember { mutableStateOf<List<LogRow>>(emptyList()) }
    var err by remember { mutableStateOf<String?>(null) }
    var confirmClear by remember { mutableStateOf(false) }
    var confirmUnlock by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val refresh = rememberRefresh()

    // Camera: one snapshot every 1.5 s while this screen is open.
    LaunchedEffect(room.id, refresh.key) {
        while (true) {
            val b = Api.snapshot(room.id)
            if (b != null) { frame = b; camDown = false } else camDown = true
            delay(1500)
        }
    }
    suspend fun loadLogs() {
        try { logs = Api.logs(room.id); err = null }
        catch (e: CancellationException) { throw e }
        catch (e: AuthException) { onLogout() }
        catch (e: Exception) { err = e.message }
    }
    LaunchedEffect(room.id, refresh.key) { while (true) { loadLogs(); delay(5000) } }
    // Battery / "Unlocking…" state.
    LaunchedEffect(room.id, refresh.key) {
        while (true) {
            try { Api.rooms().firstOrNull { it.id == room.id }?.let { cur = it } }
            catch (e: CancellationException) { throw e }
            catch (e: AuthException) { onLogout(); return@LaunchedEffect }
            catch (e: Exception) { }
            delay(4000)
        }
    }

    Column(Modifier.fillMaxSize()) {
        CyTopBar(
            start = { RoundIcon(Ic.Back, "Back", onBack); Wordmark(20.sp) },
            end = { RefreshButton(refresh.busy) { refresh.trigger() }; BatteryChip(cur.battery) }
        )
        LazyColumn(
            Modifier.weight(1f), contentPadding = PaddingValues(18.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item { Hero(if (cur.name.isBlank()) "Unoccupied" else cur.name, "Room no.", cur.id.toString()) }

            item {
                val f = frame
                val shape = RoundedCornerShape(20.dp)
                Box(
                    Modifier.fillMaxWidth().aspectRatio(4f / 3f).clip(shape).background(Color(0xFF050F1D)).border(1.dp, Cy.Line, shape),
                    contentAlignment = Alignment.Center
                ) {
                    if (f != null) Image(f.asImageBitmap(), contentDescription = "Camera", modifier = Modifier.fillMaxSize())
                    if (f == null || camDown) Text(if (f == null) "Connecting to camera…" else "Camera offline", color = Cy.Mute)
                    LiveBadge(
                        label = if (f == null) "CONNECTING" else if (camDown) "OFFLINE" else "LIVE",
                        live = f != null && !camDown,
                        modifier = Modifier.align(Alignment.TopStart).padding(12.dp)
                    )
                    Text("Room no. ${cur.id}", fontSize = 13.sp, fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.align(Alignment.BottomStart).padding(14.dp))
                }
            }

            item {
                CyCard(border = if (cur.unlockPending) Cy.Amber else Color(0x73FCB415)) {
                    Row(Modifier.padding(start = 2.dp, bottom = 12.dp), verticalAlignment = Alignment.CenterVertically) {
                        CyIcon(if (cur.unlockPending) Ic.Unlock else Ic.Lock)
                        Spacer(Modifier.width(8.dp))
                        Text(if (cur.unlockPending) "Unlocking…" else "Door is locked", fontWeight = FontWeight.Bold)
                    }
                    ActionButton(
                        if (cur.unlockPending) "Unlocking…" else "Unlock door", onClick = { confirmUnlock = true },
                        icon = Ic.Unlock, enabled = !cur.unlockPending, big = true
                    )
                }
            }

            item {
                CyCard(onClick = { onEdit(cur) }) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        IconTile(Ic.Person)
                        Spacer(Modifier.width(14.dp))
                        Column(Modifier.weight(1f)) {
                            Text("Edit tenant", fontWeight = FontWeight.ExtraBold, fontSize = 17.sp)
                            Text("Name, username & password", color = Cy.Mute, fontSize = 13.sp)
                        }
                        CyIcon(Ic.Next, tint = Cy.Mute)
                    }
                }
            }

            item {
                CyCard(onClick = { onNew(cur) }) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        IconTile(Ic.Person)
                        Spacer(Modifier.width(14.dp))
                        Column(Modifier.weight(1f)) {
                            Text("New tenant", fontWeight = FontWeight.ExtraBold, fontSize = 17.sp)
                            Text("Check in someone new · restarts time stayed", color = Cy.Mute, fontSize = 13.sp)
                        }
                        CyIcon(Ic.Next, tint = Cy.Mute)
                    }
                }
            }

            item {
                Row(Modifier.fillMaxWidth().padding(top = 8.dp), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Text("Latest logs for this unit", fontWeight = FontWeight.ExtraBold, fontSize = 17.sp)
                    OutlinedButton(
                        onClick = { confirmClear = true },
                        border = androidx.compose.foundation.BorderStroke(1.dp, Cy.Low.copy(alpha = 0.6f)),
                        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)
                    ) {
                        CyIcon(Ic.Trash, 16.dp, Cy.Low)
                        Spacer(Modifier.width(6.dp))
                        Text("Clear", color = Cy.Low, fontWeight = FontWeight.Bold)
                    }
                }
            }
            err?.let { e -> item { ErrorBox(e) } }
            if (logs.isEmpty()) item { EmptyBox("No activity logs found.") }
            items(logs) { l -> LogItem(l) }
            item { BrandFoot() }
        }
    }

    if (confirmUnlock) {
        AlertDialog(
            onDismissRequest = { confirmUnlock = false },
            containerColor = Cy.Navy2, titleContentColor = Cy.Cream, textContentColor = Cy.Mute,
            title = { Text("Unlock Room ${room.id}?", fontWeight = FontWeight.ExtraBold) },
            confirmButton = {
                TextButton(onClick = {
                    confirmUnlock = false
                    scope.launch {
                        try {
                            Api.unlock(room.id)
                            Api.rooms().firstOrNull { it.id == room.id }?.let { cur = it }
                            loadLogs()
                        }
                        catch (e: AuthException) { onLogout() }
                        catch (e: Exception) { err = e.message }
                    }
                }) { Text("Unlock", color = Cy.Amber, fontWeight = FontWeight.ExtraBold) }
            },
            dismissButton = { TextButton(onClick = { confirmUnlock = false }) { Text("Cancel", color = Cy.Mute) } }
        )
    }

    if (confirmClear) {
        AlertDialog(
            onDismissRequest = { confirmClear = false },
            containerColor = Cy.Navy2, titleContentColor = Cy.Cream, textContentColor = Cy.Mute,
            title = { Text("Delete all logs for Room ${room.id}?", fontWeight = FontWeight.ExtraBold) },
            text = { Text("Report history is kept.") },
            confirmButton = {
                TextButton(onClick = {
                    confirmClear = false
                    scope.launch {
                        try { Api.clearLogs(room.id); loadLogs() }
                        catch (e: AuthException) { onLogout() }
                        catch (e: Exception) { err = e.message }
                    }
                }) { Text("Delete", color = Cy.Low, fontWeight = FontWeight.ExtraBold) }
            },
            dismissButton = { TextButton(onClick = { confirmClear = false }) { Text("Cancel", color = Cy.Mute) } }
        )
    }
}
