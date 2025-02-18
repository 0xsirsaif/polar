import type { Meta, StoryObj } from '@storybook/react'

import PublicLayout from '@/components/Layout/PublicLayout'
import Pledge from '../components/Pledge/Pledge'
import { issue, org, repo } from './testdata'

const meta: Meta<typeof Pledge> = {
  title: 'Pages/Pledge',
  component: Pledge,
  args: {
    organization: org,
    repository: repo,
    issue: issue,
  },
}

export default meta

type Story = StoryObj<typeof Pledge>

export const Default: Story = {
  parameters: {
    chromatic: { viewports: [390, 1200] },
  },

  render: (args) => {
    return (
      <PublicLayout>
        <Pledge {...args} />
      </PublicLayout>
    )
  },
}

export const NoNameDescription: Story = {
  ...Default,
  args: {
    ...Default.args,
    organization: {
      ...org,
      pretty_name: undefined,
    },
    repository: {
      ...repo,
      description: undefined,
    },
  },
}

export const FundingGoal: Story = {
  ...Default,
  args: {
    ...Default.args,
    issue: {
      ...issue,
      funding: {
        funding_goal: { currency: 'USD', amount: 15000 },
        pledges_sum: { currency: 'USD', amount: 5000 },
      },
    },
  },
}
