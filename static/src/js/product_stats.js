//odoo.define('project_wbs.project_wbs', function (require) {
$(function () {
'use strict';
var website = openerp.website;

var svg = d3.select("svg"),
    width = +svg.attr("width"),
    height = +svg.attr("height");

var fader = function(color) { return d3.interpolateRgb(color, "#fff")(0.2); },
    color = d3.scaleOrdinal(d3.schemeCategory20.map(fader)),
    format = d3.format(",d");

var treemap = d3.treemap()
    .tile(d3.treemapResquarify)
    .size([width, height])
    .round(true)
    .paddingInner(1);

console.log('Antes de leer el json');
d3.json("/product_stats_v2/static/src/js/flare.json", function(error, data) {
  if (error) throw error;
  console.log('Proceso json');
  console.log(data);
  var productos = [];
  var sizes = [];
  var semanas = [];
  var children = [];
  $('.product').each(function(index,element) {
           productos.push($(element).text());
           });
  $('.porc_vtas').each(function(index,element) {
           sizes.push(parseFloat($(element).text()));
           });
  $('.semanas_stock').each(function(index,element) {
	   var tmp_semanas = parseFloat($(element).text());
           semanas.push(tmp_semanas);
           });

  var color = d3.scaleThreshold()
    .domain([0, 1, 2, 3, 4, 5])
    .range(["red", "red", "yellow", "yellow", "green"]);

  for (var i=0;i < productos.length;i++){
	children.push({"name": productos[i], "size": sizes[i], "semanas": semanas[i]});
	};
  var data_products = {"id":"A","name":"A","children": children};
  console.log(data_products);
  data = data_products;
  var root = d3.hierarchy(data)
      .eachBefore(function(d) { d.data.id = (d.parent ? d.parent.data.id + "." : "") + d.data.name; })
      .sum(sumBySize)
      .sort(function(a, b) { return b.height - a.height || b.value - a.value; });

  treemap(root);

  var cell = svg.selectAll("g")
    .data(root.leaves())
    .enter().append("g")
      .attr("transform", function(d) { return "translate(" + d.x0 + "," + d.y0 + ")"; });

  //cell.append("rect")
  //    .attr("id", function(d) { return d.data.id; })
  //    .attr("width", function(d) { return d.x1 - d.x0; })
  //    .attr("height", function(d) { return d.y1 - d.y0; })
  //    .attr("fill", function(d) { return color(d.parent.data.id); });
  cell.append("rect")
      .attr("id", function(d) { return d.data.id; })
      .attr("width", function(d) { return d.x1 - d.x0; })
      .attr("height", function(d) { return d.y1 - d.y0; })
      .attr("fill", function(d) { return color(d.data.semanas); });

  cell.append("clipPath")
      .attr("id", function(d) { return "clip-" + d.data.id; })
    .append("use")
      .attr("xlink:href", function(d) { return "#" + d.data.id; });

  cell.append("text")
      .attr("clip-path", function(d) { return "url(#clip-" + d.data.id + ")"; })
    .selectAll("tspan")
      .data(function(d) { return d.data.name.split(/(?=[A-Z][^A-Z])/g); })
    .enter().append("tspan")
      .attr("x", 4)
      .attr("y", function(d, i) { return 13 + i * 10; })
      .text(function(d) { return d; });

  cell.append("title")
      .text(function(d) { return d.data.id + "\n" + format(d.value); });

  d3.selectAll("input")
      .data([sumBySize, sumByCount], function(d) { return d ? d.name : this.value; })
      .on("change", changed);

  var timeout = d3.timeout(function() {
    d3.select("input[value=\"sumByCount\"]")
        .property("checked", true)
        .dispatch("change");
  }, 2000);


  function changed(sum) {
    timeout.stop();

    treemap(root.sum(sum));

    cell.transition()
        .duration(750)
        .attr("transform", function(d) { return "translate(" + d.x0 + "," + d.y0 + ")"; })
      .select("rect")
        .attr("width", function(d) { return d.x1 - d.x0; })
        .attr("height", function(d) { return d.y1 - d.y0; });
  }
});

function sumByCount(d) {
  return d.children ? 0 : 1;
}

function sumBySize(d) {
  return d.size;
}

});

