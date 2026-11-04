package com.cycierge.admin

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MaterialTheme { Surface(Modifier.fillMaxSize()) { App() } } }
    }
}

@Composable
fun App() {
    var loggedIn by remember { mutableStateOf(false) }
    var room by remember { mutableStateOf<Room?>(null) }
    BackHandler(enabled = room != null) { room = null }
    val r = room
    when {
        !loggedIn -> LoginScreen { loggedIn = true }
        r == null -> DashboardScreen(
            onOpen = { room = it },
            onLogout = { Api.logout(); loggedIn = false }
        )
        else -> RoomScreen(r, onBack = { room = null }, onLogout = { Api.logout(); room = null; loggedIn = false })
    }
}

@Composable
fun LoginScreen(onOk: () -> Unit) {
    var user by remember { mutableStateOf("") }
    var pass by remember { mutableStateOf("") }
    var err by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    Column(Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.Center) {
        Text("CyCierge Admin", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(16.dp))
        OutlinedTextField(user, { user = it }, label = { Text("Username") }, singleLine = true,
            modifier = Modifier.fillMaxWidth())
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(pass, { pass = it }, label = { Text("Password") }, singleLine = true,
            visualTransformation = PasswordVisualTransformation(), modifier = Modifier.fillMaxWidth())
        err?.let { Spacer(Modifier.height(8.dp)); Text(it, color = MaterialTheme.colorScheme.error) }
        Spacer(Modifier.height(16.dp))
        Button(enabled = !busy && user.isNotBlank() && pass.isNotEmpty(), onClick = {
            busy = true; err = null
            scope.launch {
                try {
                    if (Api.login(user.trim(), pass)) onOk() else err = "Wrong username or password"
                } catch (e: Exception) { err = e.message ?: "Can't reach the Pi" }
                busy = false
            }
        }) { Text(if (busy) "Signing in…" else "Log in") }
    }
}

@Composable
fun DashboardScreen(onOpen: (Room) -> Unit, onLogout: () -> Unit) {
    var rooms by remember { mutableStateOf<List<Room>>(emptyList()) }
    var err by remember { mutableStateOf<String?>(null) }
    var confirm by remember { mutableStateOf<Room?>(null) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(Unit) {
        while (true) {
            try { rooms = Api.rooms(); err = null }
            catch (e: AuthException) { onLogout(); return@LaunchedEffect }
            catch (e: Exception) { err = e.message ?: "Error" }
            delay(4000)
        }
    }

    Column(Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState())) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Text("Rooms", style = MaterialTheme.typography.headlineSmall)
            TextButton(onClick = onLogout) { Text("Log out") }
        }
        err?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        rooms.forEach { r ->
            Card(Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
                Column(Modifier.padding(16.dp)) {
                    Text("Room ${r.id}", style = MaterialTheme.typography.titleMedium)
                    Text("Tenant: ${r.name}")
                    Text("Since: ${r.since}")
                    Text("Battery: ${r.battery}%")
                    if (r.unlockPending) Text("Unlock sent", color = MaterialTheme.colorScheme.primary)
                    Spacer(Modifier.height(8.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(onClick = { confirm = r }) { Text("Unlock") }
                        OutlinedButton(onClick = { onOpen(r) }) { Text("Cam & logs") }
                    }
                }
            }
        }
    }

    confirm?.let { r ->
        AlertDialog(
            onDismissRequest = { confirm = null },
            title = { Text("Unlock Room ${r.id}?") },
            confirmButton = {
                TextButton(onClick = {
                    confirm = null
                    scope.launch {
                        try { Api.unlock(r.id); rooms = Api.rooms() }
                        catch (e: AuthException) { onLogout() }
                        catch (e: Exception) { err = e.message }
                    }
                }) { Text("Unlock") }
            },
            dismissButton = { TextButton(onClick = { confirm = null }) { Text("Cancel") } }
        )
    }
}

@Composable
fun RoomScreen(room: Room, onBack: () -> Unit, onLogout: () -> Unit) {
    var frame by remember { mutableStateOf<android.graphics.Bitmap?>(null) }
    var camDown by remember { mutableStateOf(false) }
    var logs by remember { mutableStateOf<List<LogRow>>(emptyList()) }
    var err by remember { mutableStateOf<String?>(null) }
    var confirmClear by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    // Camera: one snapshot every 1.5 s while this screen is open.
    LaunchedEffect(room.id) {
        while (true) {
            val b = Api.snapshot(room.id)
            if (b != null) { frame = b; camDown = false } else camDown = true
            delay(1500)
        }
    }
    suspend fun loadLogs() {
        try { logs = Api.logs(room.id); err = null }
        catch (e: AuthException) { onLogout() }
        catch (e: Exception) { err = e.message }
    }
    LaunchedEffect(room.id) { while (true) { loadLogs(); delay(5000) } }

    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            TextButton(onClick = onBack) { Text("‹ Back") }
            Text("Room ${room.id} – ${room.name}", style = MaterialTheme.typography.titleMedium)
        }
        Box(Modifier.fillMaxWidth().aspectRatio(4f / 3f).background(Color.Black), contentAlignment = Alignment.Center) {
            val f = frame
            if (f != null) Image(f.asImageBitmap(), contentDescription = "Camera", modifier = Modifier.fillMaxSize())
            if (f == null || camDown) Text(if (f == null) "Connecting to camera…" else "Camera offline", color = Color.White)
        }
        Spacer(Modifier.height(8.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Text("Activity logs", style = MaterialTheme.typography.titleMedium)
            TextButton(onClick = { confirmClear = true }) { Text("Clear") }
        }
        err?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        if (logs.isEmpty()) Text("No activity logs found.")
        LazyColumn(Modifier.weight(1f)) {
            items(logs) { l ->
                Text("${l.date}  ${l.time}  –  ${l.activity}", modifier = Modifier.padding(vertical = 4.dp))
                HorizontalDivider()
            }
        }
    }

    if (confirmClear) {
        AlertDialog(
            onDismissRequest = { confirmClear = false },
            title = { Text("Delete all logs for Room ${room.id}?") },
            confirmButton = {
                TextButton(onClick = {
                    confirmClear = false
                    scope.launch {
                        try { Api.clearLogs(room.id); loadLogs() }
                        catch (e: AuthException) { onLogout() }
                        catch (e: Exception) { err = e.message }
                    }
                }) { Text("Delete") }
            },
            dismissButton = { TextButton(onClick = { confirmClear = false }) { Text("Cancel") } }
        )
    }
}
