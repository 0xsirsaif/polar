import { DefaultFilters } from '@/components/Dashboard'
import Gatekeeper from '@/components/Dashboard/Gatekeeper/Gatekeeper'
import IssueList from '@/components/Dashboard/IssueList'
import { DashboardFilters } from '@/components/Dashboard/filters'
import BackerLayout from '@/components/Layout/BackerLayout'
import { useAuth } from '@/hooks'
import type { NextLayoutComponentType } from 'next'
import { IssueListType, IssueStatus } from 'polarkit/api/client'
import { usePersonalDashboard } from 'polarkit/hooks'
import { ReactElement } from 'react'

const Page: NextLayoutComponentType = () => {
  const { currentUser } = useAuth()

  const filters: DashboardFilters = {
    ...DefaultFilters,
    tab: IssueListType.DEPENDENCIES,
    onlyPledged: true,
  }

  const dashboardQuery = usePersonalDashboard(
    filters.tab,
    filters.q,
    [
      IssueStatus.BACKLOG,
      IssueStatus.BUILDING,
      IssueStatus.CLOSED,
      IssueStatus.IN_PROGRESS,
      IssueStatus.PULL_REQUEST,
      IssueStatus.TRIAGED,
    ],
    filters.sort,
    filters.onlyPledged,
    filters.onlyBadged,
  )
  const dashboard = dashboardQuery.data
  const totalCount = dashboard?.pages[0].pagination.total_count || undefined

  return (
    <BackerLayout>
      <IssueList
        totalCount={totalCount}
        loading={dashboardQuery.isLoading}
        dashboard={dashboard}
        filters={filters}
        onSetFilters={() => {}}
        isInitialLoading={dashboardQuery.isInitialLoading}
        isFetchingNextPage={dashboardQuery.isFetchingNextPage}
        hasNextPage={dashboardQuery.hasNextPage || false}
        fetchNextPage={dashboardQuery.fetchNextPage}
        showSelfPledgesFor={currentUser}
      />
    </BackerLayout>
  )
}

Page.getLayout = (page: ReactElement) => {
  return <Gatekeeper>{page}</Gatekeeper>
}

export default Page
