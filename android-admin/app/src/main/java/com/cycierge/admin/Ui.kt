package com.cycierge.admin

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.addPathNodes
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.time.Duration
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.LocalTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale
import kotlin.math.max

// ---------- icons (same shapes as the tenant web page, drawn from path data) ----------
private fun strokeIcon(name: String, vararg paths: String): ImageVector =
    ImageVector.Builder(name, 24.dp, 24.dp, 24f, 24f).apply {
        paths.forEach { d ->
            addPath(
                addPathNodes(d), stroke = SolidColor(Color.Black), strokeLineWidth = 2f,
                strokeLineCap = StrokeCap.Round, strokeLineJoin = StrokeJoin.Round
            )
        }
    }.build()

private const val LOCK_BODY = "M7 11h10a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-6a2 2 0 0 1 2-2z"

object Ic {
    val Lock = strokeIcon("lock", LOCK_BODY, "M8 11V8a4 4 0 0 1 8 0v3")
    val Unlock = strokeIcon("unlock", LOCK_BODY, "M8 11V8a4 4 0 0 1 7.5-2")
    val Camera = strokeIcon("camera", "M4 8h3l2-3h6l2 3h3v11H4z", "M12 9.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 1 0 0-7z")
    val Person = strokeIcon("person", "M12 4a4 4 0 1 0 0 8 4 4 0 1 0 0-8z", "M4 21c0-4 4-7 8-7s8 3 8 7")
    val Chart = strokeIcon("chart", "M5 20v-8", "M12 20V4", "M19 20v-5")
    val Logout = strokeIcon("logout", "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4", "M16 17l5-5-5-5", "M21 12H9")
    val Book = strokeIcon("book", "M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z", "M5 17a3 3 0 0 1 3-3h11")
    val Back = strokeIcon("back", "M19 12H5", "M11 6l-6 6 6 6")
    val Next = strokeIcon("next", "M9 6l6 6-6 6")
    val Prev = strokeIcon("prev", "M15 6l-6 6 6 6")
    val Trash = strokeIcon("trash", "M4 7h16", "M10 11v6", "M14 11v6", "M6 7l1 13h10l1-13", "M9 7V4h6v3")
    val Shield = strokeIcon("shield", "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z")
    val Refresh = strokeIcon("refresh", "M23 4v6h-6", "M1 20v-6h6", "M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15")
}

@Composable
fun CyIcon(v: ImageVector, size: Dp = 22.dp, tint: Color = LocalContentColor.current) {
    Icon(v, contentDescription = null, modifier = Modifier.size(size), tint = tint)
}

// ---------- building blocks ----------
@Composable
fun Wordmark(size: TextUnit = 20.sp, modifier: Modifier = Modifier) {
    Text(
        buildAnnotatedString {
            withStyle(SpanStyle(color = Cy.Amber)) { append("Cy") }
            withStyle(SpanStyle(color = Cy.Cream)) { append("Cierge") }
        },
        modifier = modifier, fontSize = size, fontWeight = FontWeight.ExtraBold, letterSpacing = (-0.5).sp
    )
}

@Composable
fun CyTopBar(start: @Composable RowScope.() -> Unit = {}, end: @Composable RowScope.() -> Unit = {}) {
    Row(
        Modifier.fillMaxWidth().background(Cy.Navy.copy(alpha = 0.92f))
            .drawBehind { drawLine(Cy.Amber, Offset(0f, size.height), Offset(size.width, size.height), 2.dp.toPx()) }
            .padding(horizontal = 18.dp, vertical = 12.dp),
        horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp), content = start)
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp), content = end)
    }
}

@Composable
fun RoundIcon(icon: ImageVector, desc: String, onClick: () -> Unit, tint: Color = Cy.Cream) {
    Box(
        Modifier.size(40.dp).clip(RoundedCornerShape(12.dp)).background(Color(0x14FFFFFF)).clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) { Icon(icon, contentDescription = desc, modifier = Modifier.size(22.dp), tint = tint) }
}

/** Round top-bar button that spins (and ignores taps) while [busy]. */
@Composable
fun RefreshButton(busy: Boolean, onClick: () -> Unit) {
    val rot = remember { Animatable(0f) }
    LaunchedEffect(busy) {
        if (busy) {
            while (true) { rot.snapTo(0f); rot.animateTo(360f, tween(900, easing = LinearEasing)) }
        } else {
            rot.snapTo(0f)
        }
    }
    Box(
        Modifier.size(40.dp).clip(RoundedCornerShape(12.dp)).background(Color(0x14FFFFFF))
            .clickable(enabled = !busy, onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        Icon(
            Ic.Refresh, contentDescription = "Refresh",
            modifier = Modifier.size(22.dp).rotate(rot.value), tint = if (busy) Cy.Amber else Cy.Cream
        )
    }
}

@Composable
fun IconTile(icon: ImageVector, size: Dp = 40.dp, tint: Color = Cy.Amber, bg: Color = Color(0x26FCB415), round: Boolean = false) {
    Box(
        Modifier.size(size).clip(if (round) CircleShape else RoundedCornerShape(12.dp)).background(bg),
        contentAlignment = Alignment.Center
    ) { CyIcon(icon, size * 0.55f, tint) }
}

@Composable
fun CyCard(
    modifier: Modifier = Modifier, border: Color = Cy.Line, onClick: (() -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit
) {
    val shape = RoundedCornerShape(20.dp)
    Column(
        modifier.fillMaxWidth().clip(shape).background(Cy.Card).border(1.dp, border, shape)
            .then(if (onClick != null) Modifier.clickable(onClick = onClick) else Modifier)
            .padding(16.dp),
        content = content
    )
}

enum class Btn { Amber, Teal, Ghost, Danger }

@Composable
fun ActionButton(
    text: String, onClick: () -> Unit, modifier: Modifier = Modifier, icon: ImageVector? = null,
    style: Btn = Btn.Amber, enabled: Boolean = true, big: Boolean = false
) {
    val shape = RoundedCornerShape(16.dp)
    val bg: Brush
    val fg: Color
    when (style) {
        Btn.Amber -> {
            bg = if (enabled) Brush.verticalGradient(listOf(Cy.Amber2, Cy.Amber)) else SolidColor(Cy.Amber.copy(alpha = 0.55f))
            fg = Cy.Navy
        }
        Btn.Teal -> { bg = Brush.verticalGradient(listOf(Cy.Teal2, Cy.Teal)); fg = Cy.Cream }
        Btn.Ghost -> { bg = SolidColor(Color.Transparent); fg = Cy.Cream }
        Btn.Danger -> { bg = SolidColor(Color.Transparent); fg = Cy.Low }
    }
    val outline = when (style) {
        Btn.Ghost -> Modifier.border(2.dp, Cy.Line, shape)
        Btn.Danger -> Modifier.border(2.dp, Cy.Low.copy(alpha = 0.6f), shape)
        else -> Modifier
    }
    Row(
        modifier.fillMaxWidth().clip(shape).background(bg).then(outline)
            .clickable(enabled = enabled, onClick = onClick)
            .padding(vertical = if (big) 20.dp else 14.dp, horizontal = 18.dp),
        horizontalArrangement = Arrangement.Center, verticalAlignment = Alignment.CenterVertically
    ) {
        if (icon != null) { CyIcon(icon, if (big) 26.dp else 22.dp, fg); Spacer(Modifier.width(10.dp)) }
        Text(text, color = fg, fontWeight = FontWeight.ExtraBold, fontSize = if (big) 21.sp else 17.sp)
    }
}

@Composable
fun BatteryChip(pct: Int) {
    val c = when { pct < 20 -> Cy.Low; pct < 50 -> Cy.Amber; else -> Cy.Ok }
    Row(
        Modifier.clip(CircleShape).background(Cy.Card).border(1.dp, if (pct < 20) Cy.Low else Cy.Line, CircleShape)
            .padding(horizontal = 12.dp, vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Canvas(Modifier.size(width = 26.dp, height = 13.dp)) {
            val sw = 2.dp.toPx()
            val tip = 4.dp.toPx()
            drawRoundRect(c, Offset.Zero, Size(size.width - tip, size.height), CornerRadius(3.dp.toPx()), style = Stroke(sw))
            val pad = sw + 1.dp.toPx()
            val inner = max(0f, (size.width - tip - 2 * pad) * pct.coerceIn(0, 100) / 100f)
            drawRect(c, Offset(pad, pad), Size(inner, size.height - 2 * pad))
            drawRect(c, Offset(size.width - 3.dp.toPx(), size.height / 2 - 2.5.dp.toPx()), Size(3.dp.toPx(), 5.dp.toPx()))
        }
        Spacer(Modifier.width(8.dp))
        Text("$pct%", color = c, fontWeight = FontWeight.ExtraBold, fontSize = 14.sp)
    }
}

/** Shows which route the app is using right now: LAN, REMOTE (Tailscale Funnel), OFFLINE. */
@Composable
fun RouteChip(modifier: Modifier = Modifier) {
    val route by Api.route.collectAsState()
    val (label, dot) = when (route) {
        "LAN" -> "LAN" to Cy.Ok
        "Funnel" -> "REMOTE" to Cy.Amber
        "OFFLINE" -> "OFFLINE" to Cy.Low
        else -> "CHECKING" to Cy.Mute
    }
    Row(
        modifier.clip(CircleShape).background(Color(0xB30B1F3A)).padding(horizontal = 10.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(Modifier.size(8.dp).clip(CircleShape).background(dot))
        Spacer(Modifier.width(6.dp))
        Text(label, color = Cy.Cream, fontSize = 11.sp, fontWeight = FontWeight.ExtraBold, letterSpacing = 1.sp)
    }
}

@Composable
fun LiveBadge(label: String, live: Boolean, modifier: Modifier = Modifier) {
    val t = rememberInfiniteTransition(label = "pulse")
    val a by t.animateFloat(0.35f, 1f, infiniteRepeatable(tween(700), RepeatMode.Reverse), label = "a")
    Row(
        modifier.clip(CircleShape).background(Color(0xB30B1F3A)).padding(horizontal = 10.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(Modifier.size(8.dp).alpha(if (live) a else 1f).clip(CircleShape).background(if (live) Cy.Low else Cy.Mute))
        Spacer(Modifier.width(6.dp))
        Text(label, color = Cy.Cream, fontSize = 11.sp, fontWeight = FontWeight.ExtraBold, letterSpacing = 1.sp)
    }
}

@Composable
fun Hero(small: String, title: String, accent: String) {
    Column(Modifier.padding(top = 2.dp, bottom = 16.dp)) {
        Text(small, color = Cy.Mute, fontSize = 14.sp)
        Text(
            buildAnnotatedString {
                append("$title ")
                withStyle(SpanStyle(color = Cy.Amber)) { append(accent) }
            },
            fontSize = 34.sp, fontWeight = FontWeight.ExtraBold, lineHeight = 38.sp, letterSpacing = (-0.5).sp
        )
    }
}

@Composable
fun ErrorBox(msg: String) {
    val shape = RoundedCornerShape(10.dp)
    Text(
        msg, color = Color(0xFFFFD0C7), fontSize = 14.sp,
        modifier = Modifier.fillMaxWidth().padding(bottom = 14.dp).clip(shape)
            .background(Cy.Low.copy(alpha = 0.15f)).border(1.dp, Cy.Low, shape).padding(horizontal = 12.dp, vertical = 8.dp)
    )
}

@Composable
fun EmptyBox(msg: String) {
    Text(
        msg, color = Cy.Mute, fontSize = 14.sp,
        modifier = Modifier.fillMaxWidth().border(1.dp, Cy.Line, RoundedCornerShape(16.dp)).padding(22.dp)
    )
}

@Composable
fun BrandFoot() {
    Column(
        Modifier.fillMaxWidth().padding(top = 30.dp)
            .drawBehind { drawLine(Cy.Line, Offset.Zero, Offset(size.width, 0f), 1.dp.toPx()) }
            .padding(top = 26.dp, bottom = 12.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        IconTile(Ic.Lock, 52.dp, Cy.Navy, Cy.Amber, round = true)
        Spacer(Modifier.height(10.dp))
        Wordmark(44.sp)
        Text("Security made smart", color = Cy.Mute, fontSize = 14.sp, modifier = Modifier.padding(top = 8.dp))
        Text(
            "LOCAL · PRIVATE · NO MONTHLY FEES", color = Cy.Amber, fontSize = 11.sp,
            fontWeight = FontWeight.ExtraBold, letterSpacing = 1.5.sp, modifier = Modifier.padding(top = 10.dp)
        )
    }
}

// ---------- text helpers (match the tenant page wording) ----------
private val MANILA: ZoneId = ZoneId.of("Asia/Manila")

/** Raw log text -> (label, kind). kind: 0 = other, 1 = tenant unlock, 2 = admin unlock. */
fun friendlyActivity(raw: String): Pair<String, Int> {
    val s = raw.trim()
    return when {
        s.startsWith("Admin", ignoreCase = true) && s.contains("Unlock", ignoreCase = true) -> "Door unlocked by admin" to 2
        s.contains("Unlock", ignoreCase = true) -> "Tenant unlocked the door" to 1
        s.isEmpty() -> "Activity" to 0
        else -> s to 0
    }
}

/** "Today, 3:42 PM" / "Yesterday, 9:10 AM" / "Nov 4, 2026, 7:05 PM" */
fun whenText(date: String, time: String): String = try {
    val dt = LocalDateTime.of(LocalDate.parse(date.trim()), LocalTime.parse(time.trim()))
    val today = LocalDate.now(MANILA)
    val t = dt.format(DateTimeFormatter.ofPattern("h:mm a", Locale.ENGLISH))
    when (dt.toLocalDate()) {
        today -> "Today, $t"
        today.minusDays(1) -> "Yesterday, $t"
        else -> dt.format(DateTimeFormatter.ofPattern("MMM d, yyyy", Locale.ENGLISH)) + ", $t"
    }
} catch (e: Exception) { "$date $time".trim() }

/** ("8 days", "22 hr 42 min") counted up from check-in, or null if unknown. [tick] only forces a recompute. */
@Suppress("UNUSED_PARAMETER")
fun stayText(since: String, tick: Int = 0): Pair<String, String>? = try {
    val d = Duration.between(LocalDateTime.parse(since.trim().replace(' ', 'T')), LocalDateTime.now(MANILA))
    val days = max(0L, d.toDays())
    (days.toString() + if (days == 1L) " day" else " days") to "${max(0L, d.toHours() % 24)} hr ${max(0L, d.toMinutes() % 60)} min"
} catch (e: Exception) { null }
