#!/bin/bash --

cd iminspect/iminspect_assets

echo "Exporting SVG to PNG"
highdpi_file=iminspect-300dpi.png
inkscape --export-png=${highdpi_file} --export-area-page --export-dpi=300 iminspect.svg

for res in 16 24 32 48 64 72 96 128 256
do
  echo "Rendering icon size $res"
  convert ${highdpi_file} -resize ${res}x${res} iminspect-${res}.png
  cp iminspect-${res}.png ~/.local/share/icons/hicolor/${res}x${res}/apps/iminspect.png
done
rm *.png

cd ../..



#TODO make separate readme
#* run this script in the correct venv folder!
#* then:
#cp iminspect.desktop.tpl ~/.local/share/applications/iminspect.desktop
##imiversion=$(cat iminspect/version.py | grep __version__ | awk '{split($0,a,"="); print a[2]}' | tr -d "\"[:space:]'")
##sed -i "s/IMIVERSION/${imiversion}/g" ~/.local/share/applications/iminspect.desktop
#venvpath=$(pwd)
#sed -i "s:IMIPATH:${venvpath}:g" ~/.local/share/applications/iminspect.desktop
#desktop-file-validate  ~/.local/share/applications/iminspect.desktop
#TODO replace icon

#https://unix.stackexchange.com/questions/281755/where-are-the-icons-in-the-alt-tab-switcher-loaded-from-how-can-i-edit-them

