local root=app.params.root
local s=app.open(root..'/source/wall_left_baseline.png')
s.layers[1].name='r6_baseline'
local layer=s:newLayer();layer.name='PixelLab_inpaint_material'
s:newCel(layer,1,Image{fromFile=root..'/source/pixellab_wall_layer.png'},Point(0,0))
s:saveAs(root..'/editable/wall_left_r10.aseprite');s:close()
local r=app.open(root..'/editable/wall_left_r10.aseprite')
app.command.SaveFileAs{filename=root..'/source/readback.png'}
app.command.SaveFileAs{filename=root..'/../../../../assets/art/room1_wall_pixellab_r10/wall_left.png'}
r:close()
