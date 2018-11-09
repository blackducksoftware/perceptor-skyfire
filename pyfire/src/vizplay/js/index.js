var margin = 20,
		padding = 2,
		diameter = 650,
		root = flareData();

var color = d3.scale.linear()
		.domain([0, depthCount(root)])
		.range(["hsl(152,80%,80%)", "hsl(228,30%,40%)"])
		.interpolate(d3.interpolateHcl);

var pack = d3.layout.pack()
		.padding(padding)
		.size([diameter, diameter])
		.value(function(d) {
				//return d.size;
			return 100;
		}),
		arc = d3.svg.arc().innerRadius(0),
		pie = d3.layout.pie;

var svg = d3.select("body").append("svg")
		.attr("width", diameter)
		.attr("height", diameter)
		.append("g")
		.attr("transform", "translate(" + diameter / 2 + "," + diameter / 2 + ")");

var focus = root,
		nodes = pack.nodes(root),
		//nodes = svg.selectAll("g.node")
		//.data(pack.nodes(root)),
		view;


var circle = svg.selectAll("circle")
		.data(nodes)
		.enter().append("circle")
		.attr("class", function(d) {
				return d.parent ? d.children ? "node" : "node node--leaf" : "node node--root";
		})
		.style("fill", function(d) {
				return d.children ? color(d.depth) : null;
		})
		.on("click", function(d) {
				if (focus !== d) zoom(d), d3.event.stopPropagation();
		});

/*
nodes.enter()
		.append("g")
		.attr("class", "node")
		.attr("transform", function(d) {
				return "translate(" + d.x + "," + d.y + ")";
		});

var arcGs = nodes.selectAll("g.arc")
		.data(function(d) {
				return pie(d[1]).map(function(m) {
						m.r = d.r;
						return m;
				});
		});
var arcEnter = arcGs.enter().append("g").attr("class", "arc");

arcEnter.append("path")
		.attr("d", function(d) {
				arc.outerRadius(d.r);
				return arc(d);
		})
		.style("fill", function(d, i) {
				return color(i);
		});
*/
/*---------------------------------------------------------------*/

var text = svg.selectAll("text")
		.data(nodes)
		.enter().append("text")
		.attr("class", "label")
		.style("fill-opacity", function(d) {
				return d.parent === root ? 1 : 0;
		})
		.style("display", function(d) {
				return d.parent === root ? null : "none";
		})
		.text(function(d) {
				return d.name;
		});

var node = svg.selectAll("circle,text");

d3.select("body")
		.on("click", function() {
				zoom(root);
		});

zoomTo([root.x, root.y, root.r * 2 + margin]);

function zoom(d) {
		var focus0 = focus;
		focus = d;

		var transition = d3.transition()
				.duration(d3.event.altKey ? 7500 : 750)
				.tween("zoom", function(d) {
						var i = d3.interpolateZoom(view, [focus.x, focus.y, focus.r * 2 + margin]);
						return function(t) {
								zoomTo(i(t));
						};
				});

		transition.selectAll("text")
				.filter(function(d) {
						return d.parent === focus || this.style.display === "inline";
				})
				.style("fill-opacity", function(d) {
						return d.parent === focus ? 1 : 0;
				})
				.each("start", function(d) {
						if (d.parent === focus) this.style.display = "inline";
				})
				.each("end", function(d) {
						if (d.parent !== focus) this.style.display = "none";
				});
}

function zoomTo(v) {
		var k = diameter / v[2];
		view = v;
		node.attr("transform", function(d) {
				return "translate(" + (d.x - v[0]) * k + "," + (d.y - v[1]) * k + ")";
		});
		circle.attr("r", function(d) {
				return d.r * k;
		});
}

/**
 * Counts JSON graph depth
 * @param {object} branch
 * @return {Number} object graph depth
 */
function depthCount(branch) {
		if (!branch.children) {
				return 1;
		}
		return 1 + d3.max(branch.children.map(depthCount));
}

d3.select(self.frameElement).style("height", diameter + "px");

/*********************************************************************/

function flareData() {
	return {
		"name": "cluster",
		"children": [
		  {
			"name": "localhost",
			"children": [
			  {
				"name": "bd",
				"children": [
				  {
					"name": "blackduck-operator-np8hb",
					"children": [
					  {
						"name": "blackduck-operator",
						"size": 40
					  },
					  {
						"name": "blackduck-operator-ui",
						"size": 40
					  }
					]
				  },
				  {
					"name": "federator-c4ghn",
					"children": [
					  {
						"name": "federator",
						"size": 40
					  }
					]
				  },
				  {
					"name": "prometheus-746db5486d-qx24r",
					"children": [
					  {
						"name": "prometheus",
						"size": 40
					  }
					]
				  }
				]
			  },
			  {
				"name": "default",
				"children": [
				  {
					"name": "docker-registry-1-p2rft",
					"children": [
					  {
						"name": "registry",
						"size": 40
					  }
					]
				  },
				  {
					"name": "persistent-volume-setup-9d8l2",
					"children": [
					  {
						"name": "setup-persistent-volumes",
						"size": 40
					  }
					]
				  },
				  {
					"name": "router-1-kdf5w",
					"children": [
					  {
						"name": "router",
						"size": 40
					  }
					]
				  }
				]
			  },
			  {
				"name": "kube-dns",
				"children": [
				  {
					"name": "kube-dns-ntv4v",
					"children": [
					  {
						"name": "kube-proxy",
						"size": 40
					  }
					]
				  }
				]
			  },
			  {
				"name": "kube-proxy",
				"children": [
				  {
					"name": "kube-proxy-qkcdf",
					"children": [
					  {
						"name": "kube-proxy",
						"size": 40
					  }
					]
				  }
				]
			  },
			  {
				"name": "kube-system",
				"children": [
				  {
					"name": "kube-controller-manager-localhost",
					"children": [
					  {
						"name": "controllers",
						"size": 40
					  }
					]
				  },
				  {
					"name": "kube-scheduler-localhost",
					"children": [
					  {
						"name": "scheduler",
						"size": 40
					  }
					]
				  },
				  {
					"name": "master-api-localhost",
					"children": [
					  {
						"name": "api",
						"size": 40
					  }
					]
				  },
				  {
					"name": "master-etcd-localhost",
					"children": [
					  {
						"name": "etcd",
						"size": 40
					  }
					]
				  }
				]
			  },
			  {
				"name": "openshift-apiserver",
				"children": [
				  {
					"name": "openshift-apiserver-2k2fk",
					"children": [
					  {
						"name": "apiserver",
						"size": 40
					  }
					]
				  }
				]
			  },
			  {
				"name": "openshift-controller-manager",
				"children": [
				  {
					"name": "openshift-controller-manager-jjvmj",
					"children": [
					  {
						"name": "c",
						"size": 40
					  }
					]
				  }
				]
			  },
			  {
				"name": "openshift-core-operators",
				"children": [
				  {
					"name": "openshift-web-console-operator-8cf4ddf7-sscdz",
					"children": [
					  {
						"name": "operator",
						"size": 40
					  }
					]
				  }
				]
			  },
			  {
				"name": "openshift-web-console",
				"children": [
				  {
					"name": "webconsole-8498798848-xh58n",
					"children": [
					  {
						"name": "webconsole",
						"size": 40
					  }
					]
				  }
				]
			  },
			  {
				"name": "opssight-test",
				"children": [
				  {
					"name": "perceptor-8mgjc",
					"children": [
					  {
						"name": "perceptor",
						"size": 40
					  }
					]
				  },
				  {
					"name": "perceptor-scanner-986st",
					"children": [
					  {
						"name": "perceptor-scanner",
						"size": 40
					  },
					  {
						"name": "perceptor-imagefacade",
						"size": 40
					  }
					]
				  },
				  {
					"name": "pod-perceiver-dbss6",
					"children": [
					  {
						"name": "pod-perceiver",
						"size": 40
					  }
					]
				  },
				  {
					"name": "prometheus-dc9854f47-7qrxg",
					"children": [
					  {
						"name": "prometheus",
						"size": 40
					  }
					]
				  },
				  {
					"name": "skyfire-8vchs",
					"children": [
					  {
						"name": "skyfire",
						"size": 40
					  }
					]
				  }
				]
			  }
			]
		  },
		  {
			"name": null,
			"children": [
			  {
				"name": "opssight-test-0",
				"children": [
				  {
					"name": "postgres-4sxgw",
					"children": [
					  {
						"name": "postgres",
						"size": 40
					  }
					]
				  }
				]
			  }
			]
		  }
		]
	  }
	  

	  
}
	
	
/*
return {
	"name": "cluster",
	"children": [
	  {
		"name": "localhost",
		"children": [
		  {
			"name": "bd",
			"children": [
			  {
				"name": "blackduck-operator-np8hb",
				"children": [
				  {
					"name": "blackduck-operator",
					"size": 40
				  },
				  {
					"name": "blackduck-operator-ui",
					"size": 40
				  }
				]
			  },
			  {
				"name": "federator-c4ghn",
				"children": [
				  {
					"name": "federator",
					"size": 40
				  }
				]
			  },
			  {
				"name": "prometheus-746db5486d-qx24r",
				"children": [
				  {
					"name": "prometheus",
					"size": 40
				  }
				]
			  }
			]
		  },
		  {
			"name": "default",
			"children": [
			  {
				"name": "docker-registry-1-p2rft",
				"children": [
				  {
					"name": "registry",
					"size": 40
				  }
				]
			  },
			  {
				"name": "persistent-volume-setup-9d8l2",
				"children": [
				  {
					"name": "setup-persistent-volumes",
					"size": 40
				  }
				]
			  },
			  {
				"name": "router-1-kdf5w",
				"children": [
				  {
					"name": "router",
					"size": 40
				  }
				]
			  }
			]
		  },
		  {
			"name": "kube-dns",
			"children": [
			  {
				"name": "kube-dns-ntv4v",
				"children": [
				  {
					"name": "kube-proxy",
					"size": 40
				  }
				]
			  }
			]
		  },
		  {
			"name": "kube-proxy",
			"children": [
			  {
				"name": "kube-proxy-qkcdf",
				"children": [
				  {
					"name": "kube-proxy",
					"size": 40
				  }
				]
			  }
			]
		  },
		  {
			"name": "kube-system",
			"children": [
			  {
				"name": "kube-controller-manager-localhost",
				"children": [
				  {
					"name": "controllers",
					"size": 40
				  }
				]
			  },
			  {
				"name": "kube-scheduler-localhost",
				"children": [
				  {
					"name": "scheduler",
					"size": 40
				  }
				]
			  },
			  {
				"name": "master-api-localhost",
				"children": [
				  {
					"name": "api",
					"size": 40
				  }
				]
			  },
			  {
				"name": "master-etcd-localhost",
				"children": [
				  {
					"name": "etcd",
					"size": 40
				  }
				]
			  }
			]
		  },
		  {
			"name": "openshift-apiserver",
			"children": [
			  {
				"name": "openshift-apiserver-2k2fk",
				"children": [
				  {
					"name": "apiserver",
					"size": 40
				  }
				]
			  }
			]
		  },
		  {
			"name": "openshift-controller-manager",
			"children": [
			  {
				"name": "openshift-controller-manager-jjvmj",
				"children": [
				  {
					"name": "c",
					"size": 40
				  }
				]
			  }
			]
		  },
		  {
			"name": "openshift-core-operators",
			"children": [
			  {
				"name": "openshift-web-console-operator-8cf4ddf7-sscdz",
				"children": [
				  {
					"name": "operator",
					"size": 40
				  }
				]
			  }
			]
		  },
		  {
			"name": "openshift-web-console",
			"children": [
			  {
				"name": "webconsole-8498798848-xh58n",
				"children": [
				  {
					"name": "webconsole",
					"size": 40
				  }
				]
			  }
			]
		  },
		  {
			"name": "opssight-test",
			"children": [
			  {
				"name": "perceptor-8mgjc",
				"children": [
				  {
					"name": "perceptor",
					"size": 40
				  }
				]
			  },
			  {
				"name": "perceptor-scanner-986st",
				"children": [
				  {
					"name": "perceptor-scanner",
					"size": 40
				  },
				  {
					"name": "perceptor-imagefacade",
					"size": 40
				  }
				]
			  },
			  {
				"name": "pod-perceiver-dbss6",
				"children": [
				  {
					"name": "pod-perceiver",
					"size": 40
				  }
				]
			  },
			  {
				"name": "prometheus-dc9854f47-7qrxg",
				"children": [
				  {
					"name": "prometheus",
					"size": 40
				  }
				]
			  },
			  {
				"name": "skyfire-8vchs",
				"children": [
				  {
					"name": "skyfire",
					"size": 40
				  }
				]
			  }
			]
		  }
		]
	  },
	  {
		"name": null,
		"children": [
		  {
			"name": "opssight-test-0",
			"children": [
			  {
				"name": "postgres-4sxgw",
				"children": [
				  {
					"name": "postgres",
					"size": 40
				  }
				]
			  }
			]
		  }
		]
	  }
	]
  }
  
}
*/
	
	