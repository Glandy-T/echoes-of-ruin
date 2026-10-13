-- Pure-color editable masters. Run each PNG with Aseprite --batch --script.
local sprite=app.activeSprite
assert(sprite, 'Open a solid-color PNG first')
sprite.layers[1].name='SOLID_COLOR_BASE'
app.command.SaveFileAs{filename=app.params['output']}
