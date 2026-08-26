import type { Meta, StoryObj } from '@storybook/react-vite';
import { HumanDecisionPanel } from './App';

const meta = {
  title: 'Engineering/HumanDecisionPanel',
  component: HumanDecisionPanel,
  parameters: { layout: 'padded' },
  args: { decisionEnabled: true, onProposal: () => undefined }
} satisfies Meta<typeof HumanDecisionPanel>;

export default meta;
type Story = StoryObj<typeof meta>;

export const BlankProfessionalDecision: Story = {};
export const SourceNotVerified: Story = { args: { decisionEnabled: false } };
