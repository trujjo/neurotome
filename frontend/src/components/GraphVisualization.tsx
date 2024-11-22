import React, { useEffect, useState, useRef } from 'react';
import NeoVis from 'neovis.js';
import { Box, Select, FormControl, InputLabel, MenuItem, Paper } from '@mui/material';

interface FilterProps {
  labels: string[];
  locations: string[];
  relationships: string[];
  systems: string[];
}

const GraphVisualization: React.FC = () => {
  const [selectedLabel, setSelectedLabel] = useState<string>('');
  const [selectedLocation, setSelectedLocation] = useState<string>('');
  const [selectedRelationship, setSelectedRelationship] = useState<string>('');
  const [selectedSystem, setSelectedSystem] = useState<string>('');
  const [filters, setFilters] = useState<FilterProps>({
    labels: [],
    locations: [],
    relationships: [],
    systems: []
  });
  
  const visRef = useRef<HTMLDivElement>(null);

  const initializeNeoVis = () => {
    const config = {
      container_id: "viz",
      server_url: process.env.REACT_APP_NEO4J_URI,
      server_user: process.env.REACT_APP_NEO4J_USER,
      server_password: process.env.REACT_APP_NEO4J_PASSWORD,
      labels: {
        [selectedLabel]: {
          caption: "name",
          size: "detail",
          sizeCypher: "CASE WHEN node.detail = 'major' THEN 30 " +
                      "WHEN node.detail = 'intermediate' THEN 20 " +
                      "ELSE 10 END"
        }
      },
      relationships: {
        [selectedRelationship]: {
          caption: true,
          thickness: 2
        }
      },
      initial_cypher: buildCypherQuery()
    };

    const viz = new NeoVis(config);
    viz.render();
  };

  const buildCypherQuery = () => {
    let query = 'MATCH (n)';
    const conditions = [];

    if (selectedLabel) conditions.push(`n:${selectedLabel}`);
    if (selectedLocation) conditions.push(`n.location = '${selectedLocation}'`);
    if (selectedSystem) conditions.push(`n.system = '${selectedSystem}'`);
    
    if (conditions.length > 0) {
      query += ' WHERE ' + conditions.join(' AND ');
    }

    if (selectedRelationship) {
      query += ` MATCH (n)-[r:${selectedRelationship}]-(m)`;
    } else {
      query += ' OPTIONAL MATCH (n)-[r]-(m)';
    }

    query += ' RETURN n, r, m';
    return query;
  };

  useEffect(() => {
    // Fetch initial filters from database
    const fetchFilters = async () => {
      // Here you would normally make API calls to get these values
      // For now using placeholder data
      setFilters({
        labels: ['Node', 'Person', 'Location'],
        locations: ['Brain', 'Spine', 'PNS'],
        relationships: ['CONNECTS_TO', 'PART_OF', 'INFLUENCES'],
        systems: ['Sensory', 'Motor', 'Integration']
      });
    };

    fetchFilters();
  }, []);

  useEffect(() => {
    if (visRef.current) {
      initializeNeoVis();
    }
  }, [selectedLabel, selectedLocation, selectedRelationship, selectedSystem]);

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <FormControl fullWidth>
          <InputLabel>Label</InputLabel>
          <Select
            value={selectedLabel}
            label="Label"
            onChange={(e) => setSelectedLabel(e.target.value)}
          >
            <MenuItem value="">None</MenuItem>
            {filters.labels.map(label => (
              <MenuItem key={label} value={label}>{label}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Location</InputLabel>
          <Select
            value={selectedLocation}
            label="Location"
            onChange={(e) => setSelectedLocation(e.target.value)}
          >
            <MenuItem value="">None</MenuItem>
            {filters.locations.map(location => (
              <MenuItem key={location} value={location}>{location}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Relationship</InputLabel>
          <Select
            value={selectedRelationship}
            label="Relationship"
            onChange={(e) => setSelectedRelationship(e.target.value)}
          >
            <MenuItem value="">None</MenuItem>
            {filters.relationships.map(rel => (
              <MenuItem key={rel} value={rel}>{rel}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>System</InputLabel>
          <Select
            value={selectedSystem}
            label="System"
            onChange={(e) => setSelectedSystem(e.target.value)}
          >
            <MenuItem value="">None</MenuItem>
            {filters.systems.map(system => (
              <MenuItem key={system} value={system}>{system}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <div id="viz" ref={visRef} style={{ height: '600px', width: '100%' }} />
    </Paper>
  );
};

export default GraphVisualization;