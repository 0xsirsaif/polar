import PublicLayout from '@/components/Layout/PublicLayout'
import OrganizationPublicPage from '@/components/Organization/OrganizationPublicPage'
import type { Meta, StoryObj } from '@storybook/react'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from 'polarkit'
import { issueRead, org, repo } from './testdata'

const meta: Meta<typeof OrganizationPublicPage> = {
  title: 'Pages/OrganizationPublicPage',
  component: OrganizationPublicPage,
}

export default meta

type Story = StoryObj<typeof OrganizationPublicPage>

const orgWithBio = {
  ...org,
  bio: "Giving open source maintainers a funded backlog. Currently in Alpha. Let's fix open source funding",
  company: 'Polar Software Inc',
  // bio?: string;
  // pretty_name?: string;
  // company?: string;
  blog: 'https://polar.sh/',
  location: 'Stockholm, Sweden',
  email: 'help@polar.sh',
  twitter_username: 'polar_sh',
}

export const Default: Story = {
  parameters: {
    chromatic: { viewports: [390, 1200] },
    themes: ['light'],
  },

  args: {
    organization: orgWithBio,
    repositories: [repo],
    issues: [
      {
        ...issueRead,
        reactions: { ...issueRead.reactions, plus_one: 1000 },
        comments: 5,
      },
      issueRead,
      {
        ...issueRead,
        title:
          'SecretStr comparison fails when field is defined with Field SecretStr comparison fails when field is defined with Field SecretStr comparison fails when field is defined with Field',
        reactions: { ...issueRead.reactions, plus_one: 0 },
      },
      issueRead,
      issueRead,
      issueRead,
    ],
  },
  render: (args) => {
    return (
      <QueryClientProvider client={queryClient}>
        <PublicLayout>
          <OrganizationPublicPage {...args} />
        </PublicLayout>
      </QueryClientProvider>
    )
  },
}

export const WithoutBio: Story = {
  ...Default,
  args: {
    organization: org,
    repositories: [repo],
    issues: [issueRead, issueRead, issueRead, issueRead, issueRead, issueRead],
  },
}

export const Dark: Story = {
  ...Default,
  parameters: {
    ...Default.parameters,
    themes: ['dark'],
  },
}
