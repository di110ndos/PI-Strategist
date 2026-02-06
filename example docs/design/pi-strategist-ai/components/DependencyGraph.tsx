import React, { useEffect, useRef, useMemo } from 'react';
import * as d3 from 'd3';
import { Team, Dependency, Feature } from '../types';

interface DependencyGraphProps {
  teams: Team[];
  dependencies: Dependency[];
}

const DependencyGraph: React.FC<DependencyGraphProps> = ({ teams, dependencies }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  // Flatten teams to get all features as nodes
  const nodes = useMemo(() => {
    const allFeatures: (Feature & { teamColor: string, teamName: string })[] = [];
    teams.forEach(t => {
      t.features.forEach(f => {
        allFeatures.push({ ...f, teamColor: t.color, teamName: t.name });
      });
    });
    return allFeatures;
  }, [teams]);

  // Map dependencies to links
  const links = useMemo(() => {
    return dependencies.map(d => ({
      source: d.fromFeatureId,
      target: d.toFeatureId,
      id: d.id
    })).filter(l => nodes.find(n => n.id === l.source) && nodes.find(n => n.id === l.target));
  }, [dependencies, nodes]);

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    const width = 800;
    const height = 600;

    // Clear previous
    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3.select(svgRef.current)
      .attr("viewBox", [0, 0, width, height]);

    // Define arrow markers
    svg.append("defs").selectAll("marker")
      .data(["end"])
      .enter().append("marker")
      .attr("id", "arrow")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 25) // Offset to not overlap node
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("fill", "#94a3b8")
      .attr("d", "M0,-5L10,0L0,5");

    const simulation = d3.forceSimulation(nodes as any)
      .force("link", d3.forceLink(links).id((d: any) => d.id).distance(150))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide().radius(40));

    const link = svg.append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", "#94a3b8")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", 2)
      .attr("marker-end", "url(#arrow)");

    const node = svg.append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .call(d3.drag<any, any>()
        .on("start", (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on("drag", (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on("end", (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }));

    // Node Circles
    node.append("circle")
      .attr("r", 20)
      .attr("fill", (d: any) => d.teamColor || '#cbd5e1')
      .attr("stroke", "#fff")
      .attr("stroke-width", 2)
      .attr("class", "cursor-pointer shadow-lg");

    // Node Labels (Points)
    node.append("text")
      .text((d: any) => d.points)
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .attr("fill", "white")
      .attr("font-size", "10px")
      .attr("font-weight", "bold")
      .attr("pointer-events", "none");

    // Node Labels (Title)
    node.append("text")
      .text((d: any) => d.title.length > 15 ? d.title.substring(0, 15) + '...' : d.title)
      .attr("x", 0)
      .attr("y", 35)
      .attr("text-anchor", "middle")
      .attr("fill", "#334155")
      .attr("font-size", "12px")
      .attr("font-weight", "500")
      .attr("class", "bg-white");

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node
        .attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [nodes, links]);

  return (
    <div className="p-8 h-full flex flex-col">
       <header className="mb-4">
          <h2 className="text-3xl font-bold text-slate-800">Visual Dependency Map</h2>
          <p className="text-slate-500 mt-1">Force-directed graph of feature interdependencies</p>
        </header>
      <div className="flex-1 bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden relative">
        <svg ref={svgRef} className="w-full h-full bg-slate-50" />
        <div className="absolute top-4 right-4 bg-white/90 p-4 rounded-lg shadow-sm border border-slate-100">
           <h4 className="text-xs font-bold text-slate-400 uppercase mb-2">Legend</h4>
           <div className="space-y-2">
              {teams.map(t => (
                 <div key={t.id} className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: t.color }}></div>
                    <span className="text-xs text-slate-600 font-medium">{t.name}</span>
                 </div>
              ))}
           </div>
        </div>
      </div>
    </div>
  );
};

export default DependencyGraph;
