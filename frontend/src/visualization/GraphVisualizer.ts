
import { Network, DataSet, Options } from 'vis-network';

export class GraphVisualizer {
    private container: HTMLElement;
    private network: Network | null = null;

    constructor(containerId: string) {
        const element = document.getElementById(containerId);
        if (!element) {
            throw new Error(`Container with id ${containerId} not found`);
        }
        this.container = element;
    }

    public visualize(data: { nodes: any[], edges: any[] }) {
        const nodes = new DataSet(data.nodes);
        const edges = new DataSet(data.edges);

        const options: Options = {
            nodes: {
                shape: 'circle',
                color: {
                    background: '#97C2FC',
                    border: '#2B7CE9',
                },
                font: {
                    color: '#343434',
                    size: 14
                }
            },
            edges: {
                color: '#848484',
                arrows: 'to',
                smooth: {
                    type: 'cubicBezier'
                }
            },
            physics: {
                enabled: false
            },
            layout: {
                hierarchical: {
                    direction: 'LR',
                    sortMethod: 'directed',
                    levelSeparation: 150
                }
            }
        };

        this.network = new Network(this.container, { nodes, edges }, options);
    }
}