import React from 'react';
import { Container, CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import GraphVisualization from './components/GraphVisualization';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
  },
});

class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return <div>Something went wrong.</div>;
    }
    return this.props.children;
  }
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ErrorBoundary>
        <Container maxWidth="lg" sx={{ mt: 4 }}>
          <GraphVisualization />
        </Container>
      </ErrorBoundary>
    </ThemeProvider>
  );
}

export default App;