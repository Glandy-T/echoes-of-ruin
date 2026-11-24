from mapping import *
face_seed=next(i for i,t in enumerate(uv) if t[:,0].min()>5 and t[:,0].max()<18 and t[:,1].min()>18 and t[:,1].max()<30 and xyz[i,:,1].min()>.85)
positions=m.attribute("POSITION");tex=m.attribute("TEXCOORD_0");edges={};neigh=[set() for _ in face]
for i,tri in enumerate(face):
    for a,b in zip(tri,np.roll(tri,1)):
        k=tuple(sorted((tuple(np.r_[positions[a],tex[a]]) for a in [a,b])))
        if k in edges:
            j=edges[k];neigh[i].add(j);neigh[j].add(i)
        else:edges[k]=i
todo=[face_seed];group={face_seed}
while todo:
    kids=neigh[todo.pop()]-group
    todo.extend(kids);group.update(kids)
group=np.asarray(sorted(group))
verts=np.unique(face[group]);print(len(group),xyz[group].min((0,1)),xyz[group].max((0,1)),uv[group].min((0,1)),uv[group].max((0,1)))

