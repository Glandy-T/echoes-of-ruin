local root=app.params.root
local s=app.open(root..'/source/layers/01_PixelLab_floor_coating.png')
s.layers[1].name='01_PixelLab_floor_coating'
for _,name in ipairs({'02_PixelLab_wall_contact','03_PixelLab_twenty_pod_contacts','04_PixelLab_four_coolant_residues'}) do
 local layer=s:newLayer();layer.name=name
 s:newCel(layer,1,Image{fromFile=root..'/source/layers/'..name..'.png'},Point(0,0))
end
s:saveAs(root..'/editable/room1_floor_r14.aseprite')
app.command.SaveFileAs{filename=root..'/source/readback_with_leaks.png'}
app.command.SaveFileAs{filename=root..'/../../../../assets/art/room1_floor_pixellab_r14/floor_with_leaks.png'}
s.layers[4].isVisible=false
app.command.SaveFileAs{filename=root..'/source/readback_aged.png'}
app.command.SaveFileAs{filename=root..'/../../../../assets/art/room1_floor_pixellab_r14/floor_aged.png'}
s:close()
