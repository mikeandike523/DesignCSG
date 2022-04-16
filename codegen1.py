def rev(n):
    if n == "above":
        return "below"
    if n == "below":
        return "above"      
    if n == "east":
        return "west"
    if n == "west":
        return "east"
    if n == "north":
        return "south"
    if n == "south":
        return "north"   
    return ""
template="""


if (node->cnumber == {cnumber}) {{
    if (node->{n1}) adjacent.push_back(node->{n1});
    if (node->{n2}) adjacent.push_back(node->{n2});
    if (node->{n3}) adjacent.push_back(node->{n3});

    if (node->prnt && node->prnt->{an1} && node->prnt->{an1}->{adj1}) {{
        adjacent.push_back(node->prnt->{an1}->{adj1});
    }}
    if (node->prnt && node->prnt->{an2} && node->prnt->{an2}->{adj2}) {{
        adjacent.push_back(node->prnt->{an2}->{adj2});
    }}
    if (node->prnt && node->prnt->{an3} && node->prnt->{an3}->{adj3}) {{
        adjacent.push_back(node->prnt->{an3}->{adj3});
    }}
}}


"""

def format_code(cnumber,n1,n2,n3,adj1,adj2,adj3):
    return template.format(cnumber=cnumber,n1=n1,n2=n2,n3=n3,an1=rev(n1),an2=rev(n2),an3=rev(n3),adj1=adj1,adj2=adj2,adj3=adj3)

combos = [

(0,"above","east","south","c4","c1","c3"),
(1,"above","west","south","c5","c0","c2"),
(2,"above","west","north","c6","c3","c1"),
(3,"above","east","north","c7","c2","c0"),

(4,"below","east","south","c0","c5","c7"),
(5,"below","west","south","c1","c4","c6"),
(6,"below","west","north","c2","c7","c5"),
(7,"below","east","north","c3","c6","c4"),


]

for combo in combos:
    print(format_code(*combo))



