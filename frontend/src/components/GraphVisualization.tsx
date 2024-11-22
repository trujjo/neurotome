import React, { useEffect, useRef } from 'react';
import { Box, Paper } from '@mui/material';
import { GraphVisualizer } from '../visualization/GraphVisualizer';

const GraphVisualization: React.FC = () => {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (containerRef.current) {
            const visualizer = new GraphVisualizer('network-graph');
            // Example network data - replace with actual data from your backend
            const networkData = {
                nodes: [
                    { id: 1, label: 'Input 1', layer: 0 },
                    { id: 2, label: 'Input 2', layer: 0 },
                    { id: 3, label: 'Hidden 1', layer: 1 },
                    { id: 4, label: 'Hidden 2', layer: 1 },
                    { id: 5, label: 'Output', layer: 2 },
                ],
                edges: [
                    { from: 1, to: 3 },
                    { from: 1, to: 4 },
                    { from: 2, to: 3 },
                    { from: 2, to: 4 },
                    { from: 3, to: 5 },
                    { from: 4, to: 5 },
                ]
            };
            visualizer.visualize(networkData);
        }
    }, []);

    return (
        <Paper elevation={3}>
            <Box
                ref={containerRef}
                id="network-graph"
                sx={{
                    width: '100%',
                    height: '600px',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center'
                }}
            />
        </Paper>
    );
};

export default GraphVisualization;