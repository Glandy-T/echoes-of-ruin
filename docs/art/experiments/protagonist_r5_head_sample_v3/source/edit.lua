local d=app.params.root
local s=app.open(d..'/../protagonist_r5_face_v2/face.aseprite')
for _,item in ipairs({{'B expression - eyelids and cheek shadow','expression'},{'Hair - restrained highlight palette','hair'}}) do
 local l=s:newLayer()
 l.name=item[1]
 s:newCel(l,1,Image{fromFile=d..'/source/'..item[2]..'.png'},Point(0,0))
end
s:saveAs(d..'/head.aseprite')
app.command.SaveFileAs{filename=d..'/skin.png'}
s:close()
