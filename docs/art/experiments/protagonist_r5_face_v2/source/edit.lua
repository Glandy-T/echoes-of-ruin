local dir=app.params.root
local s=app.open(dir..'/../protagonist_r5_pixel_skin_v1/skin.aseprite')
local layer=s:newLayer()
layer.name='B original face - UV landmark alignment'
s:newCel(layer,1,Image{fromFile=dir..'/source/face_overlay.png'},Point(0,0))
s:saveAs(dir..'/face.aseprite')
app.command.SaveFileAs{filename=dir..'/skin.png'}
s:close()
