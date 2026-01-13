// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

#version 440

// Silence precision warning for Vulkan targets
precision highp float;
precision highp int;

// Inputs from the default ShaderEffect vertex shader
layout(location = 0) in vec2 qt_TexCoord0;

layout(location = 0) out vec4 fragColor;

// Uniforms provided via ShaderEffect properties and Qt built-ins (order matches QML)
layout(std140, binding = 0) uniform ubuf {
    mat4 qt_Matrix;
    float qt_Opacity;
    highp float baseGridSize;
    highp float majorMultiplier;
    highp float minorThicknessPx;
    highp float majorThicknessPx;
    highp float featherPx;
    highp float zoomLevel;
    highp float offsetX;
    highp float offsetY;
    highp vec2 viewportSize;
    lowp vec4 minorColor;
    lowp vec4 majorColor;
    highp float minorStepCanvas;
    highp float majorStepCanvas;
    highp float showMinorFlag;
};

// Compute distance in screen pixels to nearest grid line and feather for AA.
float lineAlpha(float distPx, float thicknessPx, float featherPx_) {
    float halfT = thicknessPx * 0.5;
    return 1.0 - smoothstep(halfT, halfT + featherPx_, distPx);
}

void main() {
    // Canvas coordinates for this fragment, with (0,0) at viewport center.
    // Use interpolated texture coords (0..1) to avoid devicePixelRatio/FBO scaling differences.
    highp vec2 screenPos = qt_TexCoord0 * viewportSize;
    highp float centerX = viewportSize.x * 0.5;
    highp float centerY = viewportSize.y * 0.5;
    highp float canvasX = (screenPos.x - centerX - offsetX) / zoomLevel;
    highp float canvasY = (screenPos.y - centerY - offsetY) / zoomLevel;

    // Spacing/visibility precomputed in QML
    highp float gridSize = minorStepCanvas;
    bool showMinor = showMinorFlag > 0.5;
    highp float majorStep = majorStepCanvas;

    // Distance to nearest major grid in canvas units
    highp float gmx = abs(mod(canvasX, majorStep));
    gmx = min(gmx, majorStep - gmx);
    highp float gmy = abs(mod(canvasY, majorStep));
    gmy = min(gmy, majorStep - gmy);

    // Convert to screen pixels to keep 1px visual thickness
    highp float majorDistPx = min(gmx, gmy) * zoomLevel;
    lowp float majorA = lineAlpha(majorDistPx, majorThicknessPx, featherPx);

    lowp float minorA = 0.0;
    if (showMinor) {
        // Distance to nearest minor grid in canvas units
        highp float gx = abs(mod(canvasX, gridSize));
        gx = min(gx, gridSize - gx);
        highp float gy = abs(mod(canvasY, gridSize));
        gy = min(gy, gridSize - gy);

        highp float minorDistPx = min(gx, gy) * zoomLevel;
        minorA = lineAlpha(minorDistPx, minorThicknessPx, featherPx);
    }

    // Combine: major lines override minor where they overlap
    vec4 color = vec4(0.0);
    color = mix(color, minorColor, minorA);
    color = mix(color, majorColor, majorA);

    fragColor = color * qt_Opacity;
}

