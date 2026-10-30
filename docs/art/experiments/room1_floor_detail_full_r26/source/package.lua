local root=app.params.root
local s=app.open(root..'/source/layers/base_current_hidden.png')
s.layers[1].name='current_exact_hidden_occupied_floor_only'
local fresh=s:newLayer();fresh.name='r26_native_PixelLab_world_aligned_material'
s:newCel(fresh,1,Image{fromFile=root..'/source/layers/new_native_PixelLab_material.png'},Point(0,0))
s:saveAs(root..'/editable/room1_floor_r26.aseprite')
app.command.SaveFileAs{filename=root..'/source/readback_floor.png'}
s:close()
