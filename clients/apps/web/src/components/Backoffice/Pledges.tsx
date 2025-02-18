import { ArrowTopRightOnSquareIcon } from '@heroicons/react/20/solid'
import Link from 'next/link'
import { BackofficePledge } from 'polarkit/api/client'
import { ThinButton } from 'polarkit/components/ui'
import { useBackofficeAllPledges } from 'polarkit/hooks'
import { getCentsInDollarString } from 'polarkit/money'
import { classNames } from 'polarkit/utils'
import { useMemo } from 'react'

const Pledges = () => {
  const pledges = useBackofficeAllPledges()

  const issueList = useMemo(() => {
    const byIssue =
      pledges.data?.reduce(
        (hash: Record<string, Array<BackofficePledge>>, obj) => ({
          ...hash,
          [obj.issue.id]: (hash[obj.issue.id] || []).concat(obj),
        }),
        {},
      ) || {}

    return Object.values(byIssue)
  }, [pledges])

  return (
    <div className="space-y-4">
      {issueList.map((i) => (
        <div>
          <div className="flex gap-2">
            <Link
              className="text-blue-600"
              href={`/backoffice/issue/${i[0].issue.id}`}
            >
              {i[0].issue.repository.organization?.name}/
              {i[0].issue.repository.name}#{i[0].issue.number}
            </Link>

            <span>&quot;{i[0].issue.title}&quot;</span>

            <ThinButton
              color="gray"
              href={`https://github.com/${i[0].issue.repository.organization?.name}/${i[0].issue.repository.name}/issues/${i[0].issue.number}`}
            >
              <span>GitHub</span>
              <ArrowTopRightOnSquareIcon />
            </ThinButton>
          </div>
          <div className="flex flex-col gap-2 p-4">
            {i.map((p) => (
              <div className="flex flex-col" key={p.id}>
                <div className="flex items-center gap-2">
                  <div>
                    ${getCentsInDollarString(p.amount.amount, true, true)} from{' '}
                  </div>
                  {p.pledger?.avatar_url && (
                    <img className="h-6 w-6" src={p.pledger.avatar_url} />
                  )}
                  <div className="underline">
                    {p.pledger?.github_username ||
                      p.pledger_email ||
                      'Anonymous'}
                  </div>
                  <div
                    className={classNames(
                      'flex items-center rounded-full bg-gray-500 px-2 text-sm text-white',
                      p.state === 'disputed' || p.state === 'charge_disputed'
                        ? '!bg-red-700'
                        : '',
                      p.state === 'pending' ? '!bg-green-700' : '',
                      p.state === 'confirmation_pending' ? '!bg-blue-700' : '',
                    )}
                  >
                    {p.state}
                  </div>
                  <ThinButton
                    color="gray"
                    href={`https://dashboard.stripe.com/payments/${p.payment_id}`}
                  >
                    <span>Payment</span>
                    <ArrowTopRightOnSquareIcon />
                  </ThinButton>
                </div>
                {p.disputed_at && (
                  <div className="bg-red-700 p-2">
                    Reason: {p.dispute_reason}
                    <br />
                    At: {p.disputed_at}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

export default Pledges
