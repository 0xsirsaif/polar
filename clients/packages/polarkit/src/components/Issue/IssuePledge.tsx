import { Funding, PledgeRead, PledgeState, UserRead } from 'polarkit/api/client'
import { getCentsInDollarString } from 'polarkit/money'
import { useMemo } from 'react'
import IssueConfirmButton from './IssueConfirmButton'

interface Props {
  orgName: string
  repoName: string
  issueNumber: number
  pledges: PledgeRead[]
  onConfirmPledges: (
    orgName: string,
    repoName: string,
    issueNumber: number,
  ) => Promise<void>
  showConfirmPledgeAction: boolean
  confirmPledgeIsLoading: boolean
  funding: Funding
  showSelfPledgesFor?: UserRead
}

const IssuePledge = (props: Props) => {
  const {
    orgName,
    repoName,
    issueNumber,
    pledges,
    showConfirmPledgeAction,
    confirmPledgeIsLoading,
    showSelfPledgesFor,
  } = props

  const totalPledgeAmount = pledges.reduce(
    (accumulator, pledge) => accumulator + pledge.amount,
    0,
  )

  const confirmPledges = async () => {
    await props.onConfirmPledges(orgName, repoName, issueNumber)
  }

  const confirmable = useMemo(() => {
    return (
      pledges.some(
        (p) =>
          p.state === PledgeState.CONFIRMATION_PENDING &&
          p.authed_user_can_admin_received,
      ) && !confirmPledgeIsLoading
    )
  }, [pledges, confirmPledgeIsLoading])

  const isConfirmed = useMemo(() => {
    return (
      !confirmable &&
      pledges.some(
        (p) =>
          p.state === PledgeState.PENDING && p.authed_user_can_admin_received,
      ) &&
      !confirmPledgeIsLoading
    )
  }, [pledges, confirmPledgeIsLoading, confirmable])

  const showFundingGoal =
    props.funding?.funding_goal?.amount && props.funding.funding_goal.amount > 0

  const fundingGoalProgress =
    (totalPledgeAmount / (props.funding?.funding_goal?.amount || 0)) * 100

  const selfContribution = showSelfPledgesFor
    ? pledges
        .filter((p) => p.pledger_user_id === showSelfPledgesFor.id)
        .map((p) => p.amount)
        .reduce((a, b) => a + b, 0)
    : 0

  return (
    <>
      <div className="flex flex-row items-center justify-center space-x-4">
        {selfContribution > 0 && (
          <>
            <p className="flex-shrink-0 rounded-2xl bg-blue-800 px-3 py-1 text-sm text-blue-300 dark:bg-blue-200 dark:text-blue-700">
              You:{' '}
              <span className="whitespace-nowrap text-blue-100 dark:text-blue-900">
                ${getCentsInDollarString(selfContribution, false, true)}
              </span>
            </p>

            {showFundingGoal && (
              <div className="flex flex-col gap-1 whitespace-nowrap text-sm">
                <div>
                  <span className="text-gray-700 dark:text-gray-200">
                    ${getCentsInDollarString(totalPledgeAmount)}
                  </span>
                  <span className="text-gray-500">
                    {' '}
                    / $
                    {getCentsInDollarString(
                      props.funding.funding_goal?.amount || 0,
                      false,
                      true,
                    )}{' '}
                    funded
                  </span>
                </div>
                <div className="flex min-w-[100px] flex-row items-center overflow-hidden rounded-full">
                  <div
                    className="h-2 bg-blue-600"
                    style={{
                      width: `${fundingGoalProgress}%`,
                    }}
                  ></div>
                  <div className="h-2 flex-1 bg-gray-200 dark:bg-gray-600"></div>
                </div>
              </div>
            )}

            {!showFundingGoal && (
              <p className="text-sm text-gray-500">
                Total funding:{' '}
                <span className="whitespace-nowrap text-gray-900 dark:text-blue-400">
                  ${getCentsInDollarString(totalPledgeAmount, false, true)}
                </span>
              </p>
            )}
          </>
        )}

        {!selfContribution && (
          <p className="flex-shrink-0 rounded-2xl bg-blue-800 px-3 py-1 text-sm text-blue-300 dark:bg-blue-200 dark:text-blue-700">
            ${' '}
            <span className="whitespace-nowrap text-blue-100 dark:text-blue-900">
              {getCentsInDollarString(totalPledgeAmount, false, true)}
            </span>
            {showFundingGoal && (
              <span className="whitespace-nowrap text-blue-100/70 dark:text-blue-900/70">
                &nbsp;/ $
                {getCentsInDollarString(
                  props.funding.funding_goal?.amount || 0,
                  false,
                  true,
                )}
              </span>
            )}
          </p>
        )}

        {showConfirmPledgeAction && (
          <>
            {isConfirmed && (
              <span className="text-sm font-medium text-gray-600 dark:text-gray-500">
                Solved
              </span>
            )}
            {confirmPledgeIsLoading && (
              <span className="text-sm font-medium text-gray-600 dark:text-gray-500">
                Loading...
              </span>
            )}
            {confirmable && <IssueConfirmButton onClick={confirmPledges} />}
          </>
        )}
      </div>
    </>
  )
}

export default IssuePledge
