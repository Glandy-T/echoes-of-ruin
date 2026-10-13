-- Aseprite batch: source is a downloaded PixelLab PNG; guide is a hidden layer.
local sprite = app.open(app.params.input)
sprite.layers[1].name = 'PixelLab_raw_candidate_UNAPPROVED'
local guide = sprite:newLayer()
guide.name = 'Technical_color_guide_NOT_PRODUCTION'
sprite:newCel(guide, 1, Image{fromFile=app.params.guide}, Point(0, 0))
guide.isVisible = false
app.activeLayer = sprite.layers[1]
sprite:saveAs(app.params.output)
sprite:close()
