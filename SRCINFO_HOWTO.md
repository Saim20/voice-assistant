# Generating .SRCINFO for AUR

The `.SRCINFO` file is required for AUR packages. It contains metadata about the package extracted from the PKGBUILD.

## How to Generate .SRCINFO

After creating or updating the PKGBUILD, generate the .SRCINFO file:

```bash
makepkg --printsrcinfo > .SRCINFO
```

## When to Regenerate

You must regenerate `.SRCINFO` whenever you:
- Change the PKGBUILD
- Update package version
- Modify dependencies
- Change build options

## For AUR Maintainers

When publishing to AUR:

1. Update PKGBUILD with new version/changes
2. Generate .SRCINFO: `makepkg --printsrcinfo > .SRCINFO`
3. Commit both files:
   ```bash
   git add PKGBUILD .SRCINFO
   git commit -m "Update to version X.Y.Z"
   git push
   ```

## Example .SRCINFO

The `.SRCINFO` for this package should look similar to:

```
pkgbase = gnome-assistant
	pkgdesc = Advanced voice control for GNOME Shell with whisper.cpp offline speech recognition
	pkgver = 2.0.0
	pkgrel = 1
	url = https://github.com/Saim20/gnome-assistant
	arch = x86_64
	license = MIT
	makedepends = cmake
	makedepends = git
	makedepends = gcc
	depends = gnome-shell>=45
	depends = sdbus-cpp
	depends = jsoncpp
	depends = libpulse
	depends = ydotool
	optdepends = cuda: for NVIDIA GPU acceleration
	optdepends = vulkan-icd-loader: for Vulkan GPU acceleration (AMD/Intel/NVIDIA)
	optdepends = vulkan-headers: for Vulkan GPU acceleration build support
	source = gnome-assistant::git+https://github.com/Saim20/gnome-assistant.git
	sha256sums = SKIP

pkgname = gnome-assistant
```

## Validation

After generating, validate the .SRCINFO:

```bash
# Check syntax
makepkg --printsrcinfo | diff - .SRCINFO

# If output is empty, files match (good!)
# If there's output, regenerate .SRCINFO
```
