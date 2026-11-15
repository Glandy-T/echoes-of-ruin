-- Keep the official PixelLab result and future local retouching separable.
local base = app.open(app.params.raw)
base.layers[1].name = 'PixelLab Pro Flash - original native 256px'
local edit = base:newLayer()
edit.name = 'Aseprite local refinement - empty in v1'
base:newCel(edit, 1, Image(256,256,ColorMode.RGB), Point(0,0))
base:saveAs(app.params.output)
app.command.SaveFileAs{filename=app.params.readback}
base:close()
