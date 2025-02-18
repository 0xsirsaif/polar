import { PlusIcon } from '@heroicons/react/20/solid'
import Image from 'next/image'
import { CONFIG } from 'polarkit'
import { PrimaryButton } from 'polarkit/components/ui'
import { useStore } from 'polarkit/store'
import { classNames } from 'polarkit/utils'
import { posthog } from 'posthog-js'
import { MouseEvent, useEffect, useState } from 'react'
import screenshot from './ScreenshotDashboard.png'

const OnboardingConnectPersonalDashboard = () => {
  const isSkipped = useStore((store) => store.onboardingDashboardSkip)
  const setIsSkipped = useStore((store) => store.setOnboardingDashboardSkip)

  const hideDashboardBanner = (e: MouseEvent<HTMLButtonElement>) => {
    e.preventDefault()
    setIsSkipped(true)
  }

  const [show, setShow] = useState(false)

  useEffect(() => {
    setShow(!isSkipped)
  }, [isSkipped])

  if (!show) {
    return <></>
  }

  return (
    <>
      <div
        className={classNames(
          'flex-start mb-4 flex flex-row overflow-hidden rounded-xl bg-white shadow dark:bg-gray-800 dark:ring-1 dark:ring-gray-700',
        )}
      >
        <div className="flex-1">
          <div className="flex h-full flex-col space-y-2 p-6 pt-4">
            <h2 className="text-xl">
              Connect a repo to unlock Polar’s full potential
            </h2>
            <div className="flex-1 text-sm text-gray-500 dark:text-gray-400">
              <p>
                Interested in getting backers behind your open source efforts?
                Or looking to track issues you&apos;re dependent on and pledge
                behind them? Connect your repositories to get started.
              </p>
            </div>
            <div className="flex items-center justify-between gap-4 pt-2 lg:justify-start">
              <PrimaryButton
                color="blue"
                classNames="pl-3.5"
                fullWidth={false}
                onClick={() => {
                  posthog.capture(
                    'Connect Repository Clicked',
                    {
                      view: 'Onboarding Card Personal',
                    },
                    { send_instantly: true },
                  )
                  window.open(CONFIG.GITHUB_INSTALLATION_URL, '_blank')
                }}
              >
                <PlusIcon className="h-6 w-6" />
                <span>Connect a repository</span>
              </PrimaryButton>
              <button
                type="button"
                className="text-md text-blue-600 transition-colors duration-200 hover:text-blue-400"
                onClick={hideDashboardBanner}
              >
                Skip
              </button>
            </div>
          </div>
        </div>
        <div className="relative hidden flex-1 lg:block">
          <Image
            src={screenshot}
            alt="Polar dashboard screenshot"
            priority={true}
            className="absolute h-full w-full object-cover object-left-top"
          />
        </div>
      </div>
    </>
  )
}

export default OnboardingConnectPersonalDashboard
