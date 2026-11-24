local root=app.params.root
local sprite=app.open(root..'/source/guide.png')
sprite.layers[1].name='Tripo UV placement guide'
sprite.layers[1].isVisible=false
local art=sprite:newLayer()
art.name='PixelLab native 128'
sprite:newCel(art,1,Image{fromFile=root..'/raw/pixellab.png'},Point(0,0))
sprite:saveAs(root..'/skin.aseprite')
sprite:close()
