local root=app.params.root or 'G:/卒業制作/echoes-of-ruin/docs/art/experiments/room1_floor_contact_r8'
local sprite=app.open(root..'/source/floor_layers/floor_coating.png')
sprite.layers[1].name='01_CONTINUOUS_AGED_BLUE_GRAY_COATING'
for _,name in ipairs({'floor_perimeter_retention','floor_base_contacts','wall_floor_connected_deposit','pod_connected_contact','pod_corner_accumulation','pod_corner_mineral_ledges'}) do
 local layer=sprite:newLayer();layer.name=name
 sprite:newCel(layer,1,Image{fromFile=root..'/source/floor_layers/'..name..'.png'},Point(0,0))
end
sprite:saveAs(root..'/editable/floor_contacts_r8.aseprite')
app.command.SaveFileAs{filename=root..'/../../../../assets/art/room1_floor_contact_r8/floor_aged.png'}
for _,name in ipairs({'floor_leak_wicking','floor_leak_dark_film','floor_leak_dried_tide'}) do
 local layer=sprite:newLayer();layer.name=name
 sprite:newCel(layer,1,Image{fromFile=root..'/source/floor_layers/'..name..'.png'},Point(0,0))
end
sprite:saveAs(root..'/editable/floor_contacts_leaks_r8.aseprite')
app.command.SaveFileAs{filename=root..'/../../../../assets/art/room1_floor_contact_r8/floor_with_leaks.png'}
sprite:close()
for _,entry in ipairs({{'floor_contacts_r8','floor_aged'},{'floor_contacts_leaks_r8','floor_with_leaks'}}) do
 local read=app.open(root..'/editable/'..entry[1]..'.aseprite')
 print(entry[1]..' layers='..#read.layers)
 app.command.SaveFileAs{filename=root..'/source/readback/'..entry[2]..'.png'}
 read:close()
end
