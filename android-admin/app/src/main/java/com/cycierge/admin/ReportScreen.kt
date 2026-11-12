package com.cycierge.admin

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.CancellationException
import java.time.LocalDate

private val PERIODS = listOf("week" to "Weekly", "month" to "Monthly", "year" to "Yearly")

private fun LocalDate.shift(period: String, dir: Long): LocalDate = when (period) {
    "week" -> plusWeeks(dir)
    "month" -> plusMonths(dir)
    else -> plusYears(dir)
}

@Composable
fun ReportScreen(onBack: () -> Unit, onLogout: () -> Unit) {
    var tab by remember { mutableStateOf(0) }
    var anchor by remember { mutableStateOf(LocalDate.now()) }
    var report by remember { mutableStateOf<Report?>(null) }
    var err by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(false) }
    val period = PERIODS[tab].first
    val refresh = rememberRefresh()

    // Reload whenever the period type or the date changes, or the refresh button is pressed.
    LaunchedEffect(tab, anchor, refresh.key) {
        loading = true
        try { report = Api.report(period, anchor.toString()); err = null }
        catch (e: CancellationException) { throw e }
        catch (e: AuthException) { onLogout(); return@LaunchedEffect }
        catch (e: Exception) { err = e.message ?: "Error" }
        loading = false
    }

    Column(Modifier.fillMaxSize()) {
        CyTopBar(
            start = { RoundIcon(Ic.Back, "Back", onBack); Wordmark(20.sp) },
            end = { Text("Reports", color = Cy.Mute, fontWeight = FontWeight.Bold); RefreshButton(refresh.busy) { refresh.trigger() } }
        )
        val r = report
        LazyColumn(
            Modifier.weight(1f), contentPadding = PaddingValues(18.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item { Hero("Admin management", "Usage", "reports") }

            // Weekly / Monthly / Yearly
            item {
                Row(
                    Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).background(Cy.Card).padding(4.dp),
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    PERIODS.forEachIndexed { i, p ->
                        val sel = tab == i
                        Text(
                            p.second, textAlign = TextAlign.Center,
                            color = if (sel) Cy.Navy else Cy.Cream,
                            fontWeight = if (sel) FontWeight.ExtraBold else FontWeight.SemiBold,
                            modifier = Modifier.weight(1f).clip(RoundedCornerShape(11.dp))
                                .background(if (sel) Cy.Amber else Color.Transparent)
                                .clickable { tab = i }.padding(vertical = 10.dp)
                        )
                    }
                }
            }

            // ‹  start – end  ›
            item {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    RoundIcon(Ic.Prev, "Previous", { anchor = anchor.shift(period, -1) })
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(if (r != null) "${r.start}  –  ${r.end}" else "…", fontWeight = FontWeight.ExtraBold, fontSize = 16.sp)
                        if (r != null) Text("${r.elapsedDays} of ${r.days} days elapsed", color = Cy.Mute, fontSize = 12.sp)
                    }
                    RoundIcon(Ic.Next, "Next", { anchor = anchor.shift(period, 1) })
                }
            }
            err?.let { e -> item { ErrorBox(e) } }
            if (loading && r == null) item { Text("Loading…", color = Cy.Mute) }

            if (r != null) {
                // All rooms
                item {
                    CyCard(border = Color(0x73FCB415)) {
                        Text("All rooms", fontWeight = FontWeight.ExtraBold, fontSize = 17.sp)
                        Row(Modifier.padding(top = 8.dp), verticalAlignment = Alignment.Bottom) {
                            Text("%.1f%%".format(r.totals.occupancyPct), color = Cy.Amber, fontSize = 36.sp, fontWeight = FontWeight.ExtraBold)
                            Text("  occupancy · ${r.totals.occupiedDays} room-days", color = Cy.Mute, fontSize = 13.sp,
                                modifier = Modifier.padding(bottom = 6.dp))
                        }
                        OccupancyBar(r.totals.occupancyPct)
                        Spacer(Modifier.height(12.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Stat("Check-ins", r.totals.checkins.toString(), Modifier.weight(1f))
                            Stat("Unlocks", r.totals.unlocks.toString(), Modifier.weight(1f))
                            Stat("Detections", r.totals.detections.toString(), Modifier.weight(1f))
                        }
                        Text("Unlocks: tenant ${r.totals.byTenant} · admin ${r.totals.byAdmin}", color = Cy.Mute,
                            fontSize = 12.sp, modifier = Modifier.padding(top = 10.dp))
                    }
                }

                r.rooms.forEach { room ->
                    item(key = "sum-${room.room}") {
                        CyCard {
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                                Text("Room ${room.room}", fontWeight = FontWeight.ExtraBold, fontSize = 20.sp, color = Cy.Amber)
                                if (room.tenant.isNotBlank()) Text(room.tenant, color = Cy.Mute, fontSize = 14.sp)
                            }
                            Text("Occupancy: ${"%.1f".format(room.occupancyPct)}%  (${room.occupiedDays} of ${r.elapsedDays} days)",
                                fontSize = 14.sp, modifier = Modifier.padding(top = 8.dp, bottom = 6.dp))
                            OccupancyBar(room.occupancyPct)
                            Spacer(Modifier.height(12.dp))
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                Stat("Check-ins", room.checkins.toString(), Modifier.weight(1f))
                                Stat("Unlocks", room.unlocks.toString(), Modifier.weight(1f))
                                Stat("Detections", room.detections.toString(), Modifier.weight(1f))
                            }
                            Text("Unlocks: tenant ${room.byTenant} · admin ${room.byAdmin}", color = Cy.Mute,
                                fontSize = 12.sp, modifier = Modifier.padding(top = 10.dp))
                        }
                    }
                    item(key = "hdr-${room.room}") {
                        Column(Modifier.padding(top = 4.dp)) {
                            BucketRow(if (r.period == "year") "MONTH" else "DAY", "UNLOCKS", "DETECT.", "OCCUPIED", header = true)
                        }
                    }
                    itemsIndexed(room.buckets, key = { _, b -> "b-${room.room}-${b.label}" }) { i, b ->
                        BucketRow(b.label, b.unlocks.toString(), b.detections.toString(), b.occupiedDays.toString(), shaded = i % 2 == 0)
                    }
                }
                item { BrandFoot() }
            }
        }
    }
}

@Composable
private fun Stat(label: String, value: String, modifier: Modifier = Modifier) {
    Column(
        modifier.clip(RoundedCornerShape(14.dp)).background(Color(0x26000000)).padding(vertical = 10.dp, horizontal = 8.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(value, fontSize = 22.sp, fontWeight = FontWeight.ExtraBold)
        Text(label, color = Cy.Mute, fontSize = 11.sp)
    }
}

@Composable
private fun OccupancyBar(pct: Double) {
    val frac = (pct / 100.0).coerceIn(0.0, 1.0).toFloat()
    Box(Modifier.fillMaxWidth().height(8.dp).clip(CircleShape).background(Cy.Card)) {
        Box(Modifier.fillMaxWidth(frac).fillMaxHeight().clip(CircleShape).background(Cy.Amber))
    }
}

@Composable
private fun BucketRow(a: String, b: String, c: String, d: String, header: Boolean = false, shaded: Boolean = false) {
    val w = if (header) FontWeight.ExtraBold else FontWeight.Normal
    val color = if (header) Cy.Amber else Cy.Cream
    val size = if (header) 11.sp else 14.sp
    Row(
        Modifier.fillMaxWidth()
            .background(if (header) Color(0x330A6C72) else if (shaded) Cy.Card else Color.Transparent)
            .padding(horizontal = 10.dp, vertical = if (header) 8.dp else 6.dp)
    ) {
        Text(a, Modifier.weight(1.3f), fontWeight = w, color = color, fontSize = size)
        Text(b, Modifier.weight(1f), fontWeight = w, color = color, fontSize = size)
        Text(c, Modifier.weight(1f), fontWeight = w, color = color, fontSize = size)
        Text(d, Modifier.weight(1f), fontWeight = w, color = color, fontSize = size)
    }
}
