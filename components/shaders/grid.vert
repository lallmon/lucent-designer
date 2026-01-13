// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

#version 440

// Inputs provided by Qt's ShaderEffect vertex pipeline
layout(location = 0) in vec4 qt_Vertex;
layout(location = 1) in vec2 qt_MultiTexCoord0;

// Outputs to the fragment shader
layout(location = 0) out vec2 qt_TexCoord0;

// Standard ShaderEffect uniform block: qt_Matrix + qt_Opacity + custom uniforms
// Order must match QML property order.
layout(std140, binding = 0) uniform ubuf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float baseGridSize;
    float majorMultiplier;
    float minorThicknessPx;
    float majorThicknessPx;
    float featherPx;
    float zoomLevel;
    float offsetX;
    float offsetY;
    vec2 viewportSize;
    vec4 minorColor;
    vec4 majorColor;
    float minorStepCanvas;
    float majorStepCanvas;
    float showMinorFlag;
};

void main() {
    qt_TexCoord0 = qt_MultiTexCoord0;
    gl_Position = qt_Matrix * qt_Vertex;
}

