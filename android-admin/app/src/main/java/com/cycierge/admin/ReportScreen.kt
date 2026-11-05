package com.cycierge.admin

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
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

    // Reload whenever the period type or the date changes.
    LaunchedEffect(tab, anchor) {
        loading = true
        try { report = Api.report(period, anchor.toString()); err = null }
        catch (e: AuthException) { onLogout(); return@LaunchedEffect }
        catch (e: Exception) { err = e.message ?: "Error" }
        loading = false
    }

    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            TextButton(onClick = onBack) { Text("‹ Back") }
            Text("Reports", style = MaterialTheme.typography.titleMedium)
        }
        TabRow(selectedTabIndex = tab) {
            PERIODS.forEachIndexed { i, p -> Tab(selected = tab == i, onClick = { tab = i }, text = { Text(p.second) }) }
        }
        Row(
            Modifier.fillMaxWidth().padding(vertical = 8.dp),
            horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically
        ) {
            OutlinedButton(onClick = { anchor = anchor.shift(period, -1) }) { Text("‹") }
            val r = report
            Text(if (r != null) "${r.start}  –  ${r.end}" else "…", style = MaterialTheme.typography.titleSmall)
            OutlinedButton(onClick = { anchor = anchor.shift(period, 1) }) { Text("›") }
        }
        err?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        if (loading && report == null) Text("Loading…")

        val r = report
        if (r != null) {
            LazyColumn(Modifier.weight(1f)) {
                item {
                    Text("${r.elapsedDays} of ${r.days} days elapsed", style = MaterialTheme.typography.bodySmall)
                    Card(Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
                        Column(Modifier.padding(16.dp)) {
                            Text("All rooms", style = MaterialTheme.typography.titleMedium)
                            Text("Occupancy: ${"%.1f".format(r.totals.occupancyPct)}%  (${r.totals.occupiedDays} room-days)")
                            Text("Check-ins: ${r.totals.checkins}")
                            Text("Unlocks: ${r.totals.unlocks}  (tenant ${r.totals.byTenant} · admin ${r.totals.byAdmin})")
                            Text("Door detections: ${r.totals.detections}")
                        }
                    }
                }
                r.rooms.forEach { room ->
                    item(key = "sum-${room.room}") {
                        Card(Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
                            Column(Modifier.padding(16.dp)) {
                                Text("Room ${room.room}", style = MaterialTheme.typography.titleMedium)
                                if (room.tenant.isNotBlank()) Text("Tenant: ${room.tenant}")
                                Text("Occupancy: ${"%.1f".format(room.occupancyPct)}%  (${room.occupiedDays} of ${r.elapsedDays} days)")
                                Text("Check-ins: ${room.checkins}")
                                Text("Unlocks: ${room.unlocks}  (tenant ${room.byTenant} · admin ${room.byAdmin})")
                                Text("Door detections: ${room.detections}")
                            }
                        }
                    }
                    item(key = "hdr-${room.room}") {
                        BucketRow(if (r.period == "year") "Month" else "Day", "Unlocks", "Detect.", "Occupied", bold = true)
                        HorizontalDivider()
                    }
                    items(room.buckets, key = { "b-${room.room}-${it.label}" }) { b ->
                        BucketRow(b.label, b.unlocks.toString(), b.detections.toString(), b.occupiedDays.toString())
                    }
                }
            }
        }
    }
}

@Composable
private fun BucketRow(a: String, b: String, c: String, d: String, bold: Boolean = false) {
    val w = if (bold) FontWeight.Bold else FontWeight.Normal
    Row(Modifier.fillMaxWidth().padding(vertical = 3.dp)) {
        Text(a, Modifier.weight(1.3f), fontWeight = w)
        Text(b, Modifier.weight(1f), fontWeight = w)
        Text(c, Modifier.weight(1f), fontWeight = w)
        Text(d, Modifier.weight(1f), fontWeight = w)
    }
}
