
import React from 'react';
import { Container, CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import GraphVisualization from './components/GraphVisualization';

const theme = createTheme();

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <GraphVisualization />
      </Container>
    </ThemeProvider>
  );
}

export default App;