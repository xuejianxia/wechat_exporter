/*
The MIT License (MIT)

Copyright (c) 2014 Jianxia Xue xuejianxia@gmail.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

gssbSpeakerGraph.js
- created by Jianxia Xue, -20140601-

Suport:
- visualize the speaker temporal viscosity graph using D3's chord graph visualization layout

*/
    
var SpeakerGraph = function( container, data ){
    var width = 600,
        height = 600,
        innerRadius = Math.min(width, height) * .31,
        outerRadius = innerRadius * 1.1;

    var svg = container.append("svg")
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");
    
    var chord = new d3.layout.chord()
        .padding(.05)
        .sortSubgroups(d3.descending)

    var hsv2rgb = function(h,s,v) {
        var rgb, i, data = [];
        if (s === 0) {
            rgb = [v,v,v];
        } else {
            h = h / 60;
            i = Math.floor(h);
            data = [v*(1-s), v*(1-s*(h-i)), v*(1-s*(1-(h-i)))];
            switch(i) {
              case 0:
                rgb = [v, data[2], data[0]];
                break;
              case 1:
                rgb = [data[1], v, data[0]];
                break;
              case 2:
                rgb = [data[0], v, data[2]];
                break;
              case 3:
                rgb = [data[0], data[1], v];
                break;
              case 4:
                rgb = [data[2], data[0], v];
                break;
              default:
                rgb = [v, data[0], data[1]];
                break;
            }
        }
        return '#' + rgb.map(function(x){ 
            return ("0" + Math.round(x*255).toString(16)).slice(-2);
        }).join('');
        };

    var matrix = data.matrix;
    var nodes = data.nodes;
    var nodesT = maxNodeValue(nodes);
    var maxMatT = maxMatrixValue(matrix);
    
    chord.matrix(matrix);

    svg.append("g").append("text").text(data.label)
        .attr("x", 10)
        .attr("y", -height/2+20);

    svg.append("g").selectAll("path")
       .data(chord.groups)
       .enter().append("path")
       .style("fill", function(d) {return nodeColor(d.index); })
       .style("stroke", function(d) { return nodeColor(d.index); })
       .attr("d", d3.svg.arc().innerRadius(innerRadius).outerRadius(outerRadius))
       .on("mouseover", fade(.1))
       .on("mouseout", fade(1));

    function nodeColor( index ) {
       var h = Math.ceil(nodes[index].r/nodesT*180)+60;
       var c = hsv2rgb(h, 1, 1);
       return c;
    }

    function pathColor( sourceV, targetV ) {
	return hsv2rgb(sourceV/maxMatT*360, 1-targetV/maxMatT, 1);
    }

    var ticks =svg.append("g").selectAll("g")
	.data(chord.groups)
	.enter().append("g").selectAll("g")
	.data(groupTicks)
	.enter().append("g")
	.attr("transform", function(d) {
            return "rotate(" + (d.angle * 180 / Math.PI - 90) + ")"
                  + "translate(" + outerRadius + ",0)";
    });

    ticks.append("text")
      .attr("x", 8)
      .attr("dy", ".35em")
      .attr("transform", function(d) { return d.angle > Math.PI ? "rotate(180)    translate(-16)" : null; })
      .style("text-anchor", function(d) { return d.angle > Math.PI ? "end" : null; })
      .text(function(d) { return d.label; });

    svg.append("g")
      .attr("class", "chord")
      .selectAll("path")
      .data(chord.chords)
      .enter().append("path")
      .attr("d", d3.svg.chord().radius(innerRadius))
	.style("fill", function(d) { return pathColor(d.source.value, d.target.value); })
      .style("opacity", 1);

    function totalNodeValue( nodes ) {
       var t = 0;
       for(var i = 0; i<nodes.length; ++i)
           t += nodes[i].r;
       return t;
    }

    function maxMatrixValue( matrix ) {
	var t = matrix[0][0];
	for(var i = 0; i < matrix.length; ++i)
	    for(var j = 0; j < matrix[i].length; ++j)
		if (matrix[i][j] > t)
		    t = matrix[i][j];
	return t;
    }
    function maxNodeValue( nodes ) {
       var t = nodes[0].r;
       for(var i = 1; i<nodes.length; ++i)
           t0 = nodes[i].r
           if (t0 > t)
              t = t0;
       return t;
    }

    // Returns an array of tick angles and labels, given a group.
    function groupTicks(d) {
        var k = (d.endAngle - d.startAngle) / d.value;
        return d3.range(0, d.value, 100000).map(function(v, i) {
          return {
            angle: v * k + (d.startAngle+d.endAngle)/2,
            label: nodes[d.index].name+": "+nodes[d.index].r
          };
        });
    }

    // Returns an event handler for fading a given chord group.
    function fade(opacity) {
        return function(g, i) {
          svg.selectAll(".chord path")
              .filter(function(d) { return d.source.index != i && d.target.index != i; })
            .transition()
              .style("opacity", opacity);
        };
    }
}