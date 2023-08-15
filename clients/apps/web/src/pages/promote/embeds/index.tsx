import Gatekeeper from '@/components/Dashboard/Gatekeeper/Gatekeeper'
import LoadingScreen from '@/components/Dashboard/LoadingScreen'
import type { NextPageWithLayout } from '@/utils/next'
import { useRouter } from 'next/router'
import { ReactElement, useEffect } from 'react'

const Page: NextPageWithLayout = () => {
  const router = useRouter()
  useEffect(() => {
    router.push(`/maintainer`)
  })

  return (
    <>
      <LoadingScreen>
        <>Redirecting...</>
      </LoadingScreen>
    </>
  )
}

Page.getLayout = (page: ReactElement) => {
  return <Gatekeeper>{page}</Gatekeeper>
}

export default Page