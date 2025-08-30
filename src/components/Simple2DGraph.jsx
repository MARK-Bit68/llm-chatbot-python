import React, { useRef, useEffect, useMemo } from 'react'
import * as d3 from 'd3'

const Simple2DGraph = ({ 
  data, 
  selectedRelationships = [], 
  onNodeSelect,
  className = "" 
}) => {
  const svgRef = useRef()
  const containerRef = useRef()

  const processedData = useMemo(() => {
    if (!data) return { nodes: [], links: [] }

    // Process nodes
    const nodes = data.nodes.map(node => ({
      ...node,
      id: node.id,
      label: node.name || node.id,
      type: node.type
    }))

    // Process edges and filter by selected relationships
    const links = data.links
      .filter(edge => {
        // If no relationships are selected, show NO edges
        if (selectedRelationships.length === 0) return false
        // Otherwise, only show edges that match selected relationship types
        return selectedRelationships.includes(edge.type)
      })
      .map(edge => ({
        ...edge,
        source: edge.source,
        target: edge.target,
        type: edge.type
      }))

    return { nodes, links }
  }, [data, selectedRelationships])

  useEffect(() => {
    if (!processedData.nodes.length || !svgRef.current) return

    const container = containerRef.current
    const svg = d3.select(svgRef.current)
    
    // Clear previous content
    svg.selectAll("*").remove()

    const width = container.clientWidth
    const height = container.clientHeight

    // Create color scales
    const nodeColor = d3.scaleOrdinal()
      .domain(['Product', 'Category', 'Country', 'Plant'])
      .range(['#10B981', '#8B5CF6', '#3B82F6', '#F59E0B'])

    const linkColor = d3.scaleOrdinal()
      .domain(['BELONGS_TO', 'MANUFACTURED_AT', 'OPERATES_IN'])
      .range(['#10B981', '#EF4444', '#8B5CF6'])

    // Create a container group for zoom
    const g = svg.append("g")

    // Create force simulation
    const simulation = d3.forceSimulation(processedData.nodes)
      .force("link", d3.forceLink(processedData.links).id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(30))

    // Create links
    const link = g.append("g")
      .selectAll("line")
      .data(processedData.links)
      .join("line")
      .attr("stroke", d => linkColor(d.type))
      .attr("stroke-width", 2)
      .attr("stroke-opacity", 0.6)

    // Create nodes
    const node = g.append("g")
      .selectAll("circle")
      .data(processedData.nodes)
      .join("circle")
      .attr("r", d => {
        switch(d.type) {
          case 'Product': return 6
          case 'Category': return 10
          case 'Country': return 8
          case 'Plant': return 9
          default: return 6
        }
      })
      .attr("fill", d => nodeColor(d.type))
      .attr("stroke", "#fff")
      .attr("stroke-width", 2)
      .style("cursor", "pointer")
      .on("click", (event, d) => {
        if (onNodeSelect) onNodeSelect(d)
      })
      .on("mouseover", function(event, d) {
        d3.select(this).attr("stroke-width", 4)
        
        // Show tooltip
        const tooltip = d3.select("body").append("div")
          .attr("class", "tooltip")
          .style("position", "absolute")
          .style("background", "rgba(0,0,0,0.8)")
          .style("color", "white")
          .style("padding", "8px")
          .style("border-radius", "4px")
          .style("font-size", "12px")
          .style("pointer-events", "none")
          .style("z-index", "1000")
        
        tooltip.html(`
          <strong>${d.name || d.label}</strong><br/>
          Type: ${d.type}<br/>
          ID: ${d.id}
        `)
      })
      .on("mousemove", function(event) {
        const tooltip = d3.select(".tooltip")
        tooltip
          .style("left", (event.pageX + 10) + "px")
          .style("top", (event.pageY - 10) + "px")
      })
      .on("mouseout", function() {
        d3.select(this).attr("stroke-width", 2)
        d3.select(".tooltip").remove()
      })

    // Add node labels
    const label = g.append("g")
      .selectAll("text")
      .data(processedData.nodes)
      .join("text")
      .text(d => d.name || d.label)
      .attr("font-size", "10px")
      .attr("fill", "white")
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .style("pointer-events", "none")

    // Update positions on simulation tick
    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y)

      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y)

      label
        .attr("x", d => d.x)
        .attr("y", d => d.y)
    })

    // Add zoom behavior with proper D3.js v7 implementation
    const zoom = d3.zoom()
      .scaleExtent([0.1, 10]) // Limit zoom scale
      .on("zoom", (event) => {
        g.attr("transform", event.transform)
      })

    svg.call(zoom)

    // Store zoom behavior for reset - use a more reliable approach
    const zoomBehavior = svg.node().__zoom
    if (zoomBehavior) {
      svg.node().__zoomBehavior = zoomBehavior
    }

    // Cleanup
    return () => {
      simulation.stop()
      d3.select(".tooltip").remove()
    }
  }, [processedData, onNodeSelect])

  // Reset view function with proper D3.js v7 API
  const resetView = () => {
    const svg = d3.select(svgRef.current)
    if (svg.node() && svg.node().__zoomBehavior) {
      // Reset zoom and center the view using the stored zoom behavior
      try {
        svg.transition().duration(750).call(
          svg.node().__zoomBehavior.transform,
          d3.zoomIdentity
        )
      } catch (error) {
        // Fallback: manually reset the transform
        const g = svg.select("g")
        g.transition().duration(750).attr("transform", "translate(0,0) scale(1)")
      }
    }
  }

  if (!data) {
    return (
      <div className={`flex items-center justify-center h-full bg-gray-900 ${className}`}>
        <div className="text-white text-center">
          <div className="w-12 h-12 mx-auto mb-4 text-gray-400">📊</div>
          <p>No graph data available</p>
        </div>
      </div>
    )
  }

  return (
    <div ref={containerRef} className={`relative w-full h-full bg-gray-900 ${className}`}>
      {/* Controls */}
      <div className="absolute top-4 left-4 z-10 flex gap-2">
        <button
          onClick={resetView}
          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm"
        >
          Reset View
        </button>
      </div>

      {/* Legend */}
      <div className="absolute top-4 right-4 z-10 bg-black/80 text-white p-4 rounded-lg">
        <h3 className="font-bold mb-2">Node Types</h3>
        <div className="space-y-1 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span>Products</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-purple-500"></div>
            <span>Categories</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500"></div>
            <span>Countries</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-500"></div>
            <span>Plants</span>
          </div>
        </div>
      </div>

      {/* Graph */}
      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        style={{ background: 'transparent' }}
      />
    </div>
  )
}

export default Simple2DGraph
