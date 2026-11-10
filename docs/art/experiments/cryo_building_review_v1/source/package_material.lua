local dir = app.params.layer_dir
local sprite = app.open(dir .. '/base.png')
sprite.layers[1].name = 'Exact native surface layout'
local ai = sprite:newLayer()
ai.name = 'PixelLab native painting and material ageing'
sprite:newCel(ai, 1, Image{fromFile=dir .. '/ai.png'}, Point(0,0))
local edges = sprite:newLayer()
edges.name = 'Exact protected geometry and seams (no added weathering)'
sprite:newCel(edges, 1, Image{fromFile=dir .. '/protected.png'}, Point(0,0))
local local_edit = sprite:newLayer()
local_edit.name = 'Local cleanup - duplicated marks / invented hardware only'
sprite:newCel(local_edit, 1, Image{fromFile=dir .. '/local.png'}, Point(0,0))
sprite:saveAs(app.params.output)
app.command.SaveFileAs{filename=dir .. '/readback.png'}
sprite:close()
