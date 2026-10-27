local root=app.params.root or 'G:/卒業制作/echoes-of-ruin/docs/art/experiments/room1_surface_full_r5'
local sprite=app.open(root..'/source/floor_layers/floor_coating.png')
sprite.layers[1].name='01_CONTINUOUS_AGED_BLUE_GRAY_COATING'
for _,name in ipairs({'floor_perimeter_retention','floor_base_contacts'}) do
 local layer=sprite:newLayer();layer.name=name
 sprite:newCel(layer,1,Image{fromFile=root..'/source/floor_layers/'..name..'.png'},Point(0,0))
end
sprite:saveAs(root..'/editable/floor_aged_r5.aseprite')
app.command.SaveFileAs{filename=root..'/../../../../assets/art/room1_surface_full_r5/floor_aged.png'}
for _,name in ipairs({'floor_leak_wicking','floor_leak_dark_film','floor_leak_dried_tide'}) do
 local layer=sprite:newLayer();layer.name=name
 sprite:newCel(layer,1,Image{fromFile=root..'/source/floor_layers/'..name..'.png'},Point(0,0))
end
sprite:saveAs(root..'/editable/floor_leaks_r5.aseprite')
app.command.SaveFileAs{filename=root..'/../../../../assets/art/room1_surface_full_r5/floor_with_leaks.png'}
sprite:close()
