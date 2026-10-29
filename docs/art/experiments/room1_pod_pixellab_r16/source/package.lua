local root=app.params.root
local names={'shared/interior','shared/mattress','shared/section'}
local variants=app.params.variants or 'abcd'
for i=1,#variants do
 local v=string.sub(variants,i,i)
 for _,key in ipairs({'lid','shell_side','shell_end'}) do table.insert(names,'variant_'..v..'/'..key) end
end
for _,name in ipairs(names) do
 local s=app.open(root..'/source/layers/'..name..'_base.png');s.layers[1].name='clean_structure_without_old_aging'
 local layer=s:newLayer();layer.name='PixelLab_material_age'
 s:newCel(layer,1,Image{fromFile=root..'/source/layers/'..name..'_PixelLab.png'},Point(0,0))
 local id=s:newLayer();id.name='functional_sample_P12_ID'
 s:newCel(id,1,Image{fromFile=root..'/source/layers/'..name..'_functional_ID.png'},Point(0,0))
 local target=string.gsub(name,'/','_')
 s:saveAs(root..'/editable/'..target..'_r16.aseprite')
 app.command.SaveFileAs{filename=root..'/source/readback_'..target..'.png'}
 app.command.SaveFileAs{filename=root..'/../../../../assets/art/room1_pod_pixellab_r16/'..name..'.png'}
 s:close()
end
