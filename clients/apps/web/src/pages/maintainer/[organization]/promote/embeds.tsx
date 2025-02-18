import Gatekeeper from '@/components/Dashboard/Gatekeeper/Gatekeeper'
import { FundOurBacklog } from '@/components/Embed/FundOurBacklog'
import { SeeksFundingShield } from '@/components/Embed/SeeksFundingShield'
import DashboardLayout from '@/components/Layout/DashboardLayout'
import CopyToClipboardInput from '@/components/UI/CopyToClipboardInput'
import LabeledRadioButton from '@/components/UI/LabeledRadioButton'
import { useCurrentOrgAndRepoFromURL } from '@/hooks/org'
import { NextLayoutComponentType } from 'next'
import Head from 'next/head'
import { ShadowBox } from 'polarkit/components/ui'
import { useSearchIssues } from 'polarkit/hooks'
import { ReactElement, useState } from 'react'

const Page: NextLayoutComponentType = () => {
  const { org, isLoaded } = useCurrentOrgAndRepoFromURL()

  const fundingYAML = `custom: ["https://polar.sh/${org?.name}"]`

  const issues = useSearchIssues({
    organizationName: org?.name,
    haveBadge: true,
  })

  const [currentEmbedTab, setCurrentEmbedTab] = useState('Issues')

  if (!org && isLoaded) {
    return (
      <>
        <div className="mx-auto mt-32 flex max-w-[1100px] flex-col items-center">
          <span>Organization not found</span>
          <span>404 Not Found</span>
        </div>
      </>
    )
  }

  const previews: Record<string, ReactElement> = {
    Issues: <FundOurBacklog issues={issues.data?.items || []} />,
    Shield: (
      <div className="w-fit">
        <SeeksFundingShield count={issues.data?.items?.length || 0} />
      </div>
    ),
  }

  const embedCodes: Record<string, string> = {
    Issues: `<a href="https://polar.sh/${org?.name}"><img src="https://polar.sh/embed/fund-our-backlog.svg?org=${org?.name}" /></a>`,
    Shield: `<a href="https://polar.sh/${org?.name}"><img src="https://polar.sh/embed/seeks-funding-shield.svg?org=${org?.name}" /></a>`,
  }

  return (
    <>
      <Head>
        <title>Polar | Promote {org?.name} repository</title>
      </Head>

      <DashboardLayout showSidebar={true}>
        <div className="space-y-4">
          <h2 className="text-lg text-gray-900 dark:text-gray-400">
            Github Sponsors
          </h2>
          <p className="text-sm text-gray-500">
            Make sure to link to your public funding page from Github&apos;s
            Sponsor section.
          </p>
          <ShadowBox>
            <div className="flex flex-col gap-4">
              <h3 className="font-medium text-gray-500">
                Link to your Polar funding page
              </h3>
              <div className="max-w-[600px]">
                <CopyToClipboardInput id="github-funding" value={fundingYAML} />
              </div>
              <div className="rounded-md border border-blue-100 bg-blue-50 py-2 px-4 text-gray-700 dark:border-blue-700/50 dark:bg-blue-800/50 dark:text-gray-400">
                Follow the instructions{' '}
                <a
                  className="font-bold text-blue-500"
                  href="https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/displaying-a-sponsor-button-in-your-repository"
                >
                  here
                </a>{' '}
                and paste the above in your FUNDING.yaml
              </div>
            </div>
          </ShadowBox>
          <h2 className="pt-8 text-lg text-gray-900 dark:text-gray-400">
            Readme embeds
          </h2>
          <p className="text-sm text-gray-500">
            Embed the Polar SVG in your README or on your website to showcase
            issues that you&apos;re seeking funding for.
          </p>
          <ShadowBox>
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <h3 className="font-medium text-gray-500">Preview</h3>

                <LabeledRadioButton
                  values={['Issues', 'Shield']}
                  value={currentEmbedTab}
                  onSelected={setCurrentEmbedTab}
                />
              </div>

              <div className="flex w-full justify-center rounded-md border border-gray-200 bg-gray-50 p-8 dark:border-gray-800 dark:bg-gray-700">
                {previews[currentEmbedTab] || <></>}
              </div>

              <h3 className="font-medium text-gray-500">Embed code</h3>
              <div className="max-w-[600px]">
                <CopyToClipboardInput
                  id="embed-svg"
                  value={embedCodes[currentEmbedTab] || ''}
                />
              </div>
            </div>
          </ShadowBox>
        </div>
      </DashboardLayout>
    </>
  )
}

Page.getLayout = (page: ReactElement) => {
  return (
    <Gatekeeper>
      <>{page}</>
    </Gatekeeper>
  )
}

export default Page
