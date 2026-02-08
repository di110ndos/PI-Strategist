import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from '../App';

describe('App', () => {
  it('renders the PI Strategist logo text', () => {
    render(<App />);
    const logos = screen.getAllByText('PI Strategist');
    expect(logos.length).toBeGreaterThan(0);
  });

  it('renders navigation links', () => {
    render(<App />);
    // Desktop nav links
    const analyzeLinks = screen.getAllByText('Analyze');
    expect(analyzeLinks.length).toBeGreaterThan(0);
    const dedLinks = screen.getAllByText('DED');
    expect(dedLinks.length).toBeGreaterThan(0);
  });
});
