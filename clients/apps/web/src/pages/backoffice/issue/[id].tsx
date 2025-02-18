import { ArrowTopRightOnSquareIcon } from '@heroicons/react/20/solid'
import type { NextLayoutComponentType } from 'next'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { ThinButton } from 'polarkit/components/ui'
import {
  useBackofficeIssue,
  useBackofficePledgeRewardTransfer,
  useBackofficeRewards,
} from 'polarkit/hooks'
import { getCentsInDollarString } from 'polarkit/money'
import { classNames } from 'polarkit/utils'
import { ReactElement } from 'react'
import Topbar from '../../../components/Shared/Topbar'

const Page: NextLayoutComponentType & { theme?: string } = () => {
  const router = useRouter()
  const { id } = router.query

  const issue = useBackofficeIssue(typeof id === 'string' ? id : undefined)

  const rewards = useBackofficeRewards(typeof id === 'string' ? id : undefined)
  const rewardsData = rewards.data?.items || []

  const pledgeRewardCreateTransfer = useBackofficePledgeRewardTransfer()

  const createTransfer = async (pledgeId: string, issueRewardId: string) => {
    try {
      await pledgeRewardCreateTransfer.mutateAsync({
        pledgeId,
        issueRewardId,
      })
    } catch (e) {
      alert(JSON.stringify(e, null, 2))
    }
  }

  return (
    <div>
      <h2 className="text-2xl">Issue</h2>

      <table>
        <tbody>
          <tr>
            <td className="font-bold">Issue</td>
            <td>
              <a
                className="text-blue-600"
                href={`https://github.com/${issue.data?.repository.organization?.name}/${issue.data?.repository.name}/issues/${issue.data?.number}`}
              >
                {issue.data?.title}
              </a>
            </td>
          </tr>
          <tr>
            <td className="font-bold">State</td>
            <td>{issue.data?.state}</td>
          </tr>
          <tr>
            <td className="font-bold">Funding</td>
            <td>
              <pre>{JSON.stringify(issue.data?.funding, null, 0)}</pre>
            </td>
          </tr>
        </tbody>
      </table>

      <h3 className="mt-9 text-xl">Rewards</h3>

      <div className="flex flex-col gap-2">
        {rewardsData.map((r) => (
          <div className="flex gap-2">
            <div>
              ${getCentsInDollarString(r.amount.amount, true, true)}{' '}
              <span className="text-gray-500">
                (of $
                {getCentsInDollarString(r.pledge.amount.amount, true, true)})
              </span>{' '}
              to
            </div>
            {r.user && (
              <div>
                <span className="underline">{r.user.username}</span> [user]
              </div>
            )}
            {r.organization && (
              <div>
                <span className="underline">{r.organization.name}</span> [org]
              </div>
            )}
            <div>
              from{' '}
              <span className="underline">
                {r.pledge.pledger?.name || 'Anonymous'}
              </span>
            </div>
            <div
              className={classNames(
                'flex items-center rounded-full bg-gray-500 px-2 text-sm text-white',
                r.state === 'pending' ? '!bg-blue-700' : '',
                r.state === 'paid' ? '!bg-green-700' : '',
              )}
            >
              {r.state}
            </div>
            {r.transfer_id && (
              <ThinButton
                color="gray"
                href={`https://dashboard.stripe.com/connect/transfers/${r.transfer_id}`}
              >
                <span>Transfer</span>
                <ArrowTopRightOnSquareIcon />
              </ThinButton>
            )}
            {!r.transfer_id && (
              <ThinButton
                color="green"
                onClick={() => createTransfer(r.pledge.id, r.issue_reward_id)}
              >
                <span>Create Transfer</span>
              </ThinButton>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

Page.getLayout = (page: ReactElement) => {
  return (
    <>
      <Topbar
        customLogoTitle="Backoffice"
        logoPosition="center"
        isFixed={false}
      ></Topbar>
      <div className="mx-auto max-w-7xl p-4">
        <Link href="/backoffice" className="text-black underline">
          &lArr; Back
        </Link>
        {page}
      </div>
    </>
  )
}

Page.theme = 'light'

export default Page
