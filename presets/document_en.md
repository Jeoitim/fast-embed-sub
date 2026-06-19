English | [简体中文文档](document.md)

# Minimalist Subtitle Embedding Tool - Preset Authoring Guide

This software uses a pure data-driven preset system. Any `.txt` file placed in the `presets/` directory will be parsed automatically as an option in the user interface.

## Modular Preset Configuration Sharing Philosophy

The core value of Fast Embed Sub lies in its **modular preset configuration sharing mechanism**. We believe that high-quality encoding parameters should be shared and reused rather than having everyone test and adjust parameters repeatedly.

### Why Modular Presets?

- **Professional Parameter Reuse**: Allows experienced users to package and share their finely tuned parameters.
- **Zero Learning Cost**: Ordinary users only need to download preset files to get professional-quality video results instantly.
- **Instant Implementation**: Get the ideal encoding results in one click without knowing complex FFmpeg details.
- **Continuous Optimization**: The community can continuously refine and share better preset configurations.

### How to Get and Share Presets?

**Get Presets:**
1. Visit the preset sharing community or GitHub repository.
2. Download the needed `.txt` preset files.
3. Put them directly into the `presets/` folder of the application.
4. Restart the software to see them in the UI dropdown.

**Share Presets:**
1. Save your tested presets into a `.txt` file.
2. Upload it to preset sharing platforms.
3. Include detailed descriptions, usage, and quality previews.
4. Mark the target scenario (such as web upload, local archiving, etc.).

## Preset File Format

The preset file must contain two sections:
1. **First line (required)**: Description beginning with `#`. This text is displayed in the description card under the preset dropdown in the UI.
2. **Second line and onwards**: The actual command line template.

### Supported Placeholder Variables

When authoring your commands, use the following placeholder variables. The software will automatically replace them with the actual paths during execution:

- `{input_v}`: Source video file path.
- `{input_s}`: Source subtitle file path (Windows disk prefix and backslash escaping is auto-handled; you can place it directly in filters).
- `{output_dir}`: Output directory path.
- `{filename}`: Output filename (without extension).
- `{format}`: Output format (container extension, without the leading dot). Note: You can use `{format:webm}` in the preset to force a specific format, meaning that even if the user selects another format in the UI, the output container will be forced to webm.

### Path Conventions

Always use `components/ffmpeg.exe` to call the FFmpeg encoder; the software will automatically resolve it to an absolute path.

### Output Path Conventions

Always specify your output path using the `{output_dir}/{filename}.{format}` combination. Do not use a standalone `{output}` placeholder as it is not defined.

## Examples & Common Parameter Reference

```
# Suitable for video upload sites: Fast speed, extremely high quality (CRF 18), medium-large size, audio copy.
components/ffmpeg.exe -i "{input_v}" -vf "subtitles={input_s}" -c:v libx264 -preset fast -crf 18 -c:a copy -y "{output_dir}/{filename}.{format}"
```

```
# VP9 encoding, high quality, smaller file size
components/ffmpeg.exe -i "{input_v}" -vf "subtitles={input_s}" -c:v libvpx-vp9 -b:v 0 -crf 30 -c:a libopus -b:a 128k -y "{output_dir}/{filename}.{format}"
```

## **Example of Forcing WebM Format**

```
# VP9 encoding, forced webm container format
components/ffmpeg.exe -i "{input_v}" -vf "subtitles={input_s}" -c:v libvpx-vp9 -b:v 0 -crf 30 -c:a libopus -b:a 128k -y "{output_dir}/{filename}.{format:webm}"
```
