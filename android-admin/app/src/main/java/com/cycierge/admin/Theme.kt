package com.cycierge.admin

import androidx.compose.foundation.background
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color

/** Brochure palette (same values as php/cycierge/user/style.css). */
object Cy {
    val Navy = Color(0xFF0B1F3A)
    val Navy2 = Color(0xFF13294A)
    val Teal = Color(0xFF0A6C72)
    val Teal2 = Color(0xFF0F868D)
    val Amber = Color(0xFFFCB415)
    val Amber2 = Color(0xFFFFCF5C)
    val Cream = Color(0xFFFFF8E8)
    val Mute = Color(0xFF9CC3C6)
    val Violet = Color(0xFF4A1FB8)
    val Ok = Color(0xFF5FE0B0)
    val Low = Color(0xFFFF7A6B)
    val Line = Color(0x479CC3C6)   // 28% mute
    val Card = Color(0x12FFFFFF)   // 7% white
}

private val scheme = darkColorScheme(
    primary = Cy.Amber, onPrimary = Cy.Navy,
    secondary = Cy.Teal2, onSecondary = Cy.Cream,
    background = Cy.Navy, onBackground = Cy.Cream,
    surface = Cy.Navy2, onSurface = Cy.Cream,
    surfaceVariant = Cy.Navy2, onSurfaceVariant = Cy.Mute,
    error = Cy.Low, onError = Cy.Navy
)

@Composable
fun CyTheme(content: @Composable () -> Unit) = MaterialTheme(colorScheme = scheme, content = content)

fun Modifier.cyBackground(): Modifier = background(
    Brush.linearGradient(listOf(Color(0xFF1B1A55), Cy.Navy, Color(0xFF0A3B4A)))
)
