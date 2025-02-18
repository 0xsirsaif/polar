import { useAuth } from '@/hooks'
import Link from 'next/link'
import {
  Checkbox,
  Input,
  PrimaryButton,
  RedBanner,
  ShadowBox,
} from 'polarkit/components/ui'
import { useInviteClaimCode, useUserAcceptTermsOfService } from 'polarkit/hooks'
import { ChangeEvent, useMemo, useState } from 'react'
import TakeoverBox from './TakeoverBox'
import TakeoverHeader from './TakeoverHeader'

const InviteOnly = () => {
  const [code, setCode] = useState('')
  const [joinLoading, setJoinLoading] = useState(false)
  const [boxFadeOut, setBoxFadeOut] = useState(false)

  const claimCode = useInviteClaimCode()

  const onInputUpdated = (value: string) => {
    setCode(value)
  }

  const [showErrorBanner, setShowErrorBanner] = useState(false)
  const { reloadUser } = useAuth()

  const acceptTerms = useUserAcceptTermsOfService()

  const [approvedTos, setApprovedTos] = useState(false)
  const onChangeAcceptTos = (e: ChangeEvent<HTMLInputElement>) => {
    setApprovedTos(e.target.checked)
  }

  const doClaimCode = async () => {
    const res = await claimCode.mutateAsync({ code: code })
    if (res && res.status === true) {
      return true
    } else {
      throw new Error('invalid code')
    }
  }

  const doAcceptTerms = async () => {
    const res = await acceptTerms.mutateAsync()
    if (res && res.accepted_terms_of_service === true) {
      return true
    } else {
      throw new Error('failed to accept terms')
    }
  }

  const onJoinClick = async (event: React.MouseEvent<HTMLButtonElement>) => {
    setJoinLoading(true)
    setShowErrorBanner(false)

    try {
      await doAcceptTerms()
      await doClaimCode()

      await new Promise((r) => setTimeout(r, 500))

      setJoinLoading(false)
      setBoxFadeOut(true)

      await new Promise((r) => setTimeout(r, 500))

      await reloadUser()

      setJoinLoading(false)
    } catch (e) {
      setBoxFadeOut(false)
      setShowErrorBanner(true)
      setJoinLoading(false)
      console.error('err', e)
    }
  }

  const joinDisabled = useMemo(() => {
    return code.length < 4 || !approvedTos
  }, [code, approvedTos])

  return (
    <InviteOnlyBox
      fadeOutTakeover={boxFadeOut}
      showErrorBanner={showErrorBanner}
      acceptedTerms={approvedTos}
      onChangeAcceptedTerms={onChangeAcceptTos}
      onInviteCodeUpdated={onInputUpdated}
      joinDisabled={joinDisabled}
      joinLoading={joinLoading}
      onContinueClick={onJoinClick}
    />
  )
}

export default InviteOnly

export const InviteOnlyBox = (props: {
  fadeOutTakeover: boolean
  showErrorBanner: boolean
  acceptedTerms: boolean
  onChangeAcceptedTerms: (e: React.ChangeEvent<HTMLInputElement>) => void
  onInviteCodeUpdated: (v: string) => void
  joinDisabled: boolean
  joinLoading: boolean
  onContinueClick: (e: React.MouseEvent<HTMLButtonElement>) => void
}) => {
  return (
    <TakeoverBox fadeOut={props.fadeOutTakeover && !props.showErrorBanner}>
      <>
        <TakeoverHeader>
          <>Welcome to Polar</>
        </TakeoverHeader>

        {props.showErrorBanner && (
          <RedBanner>
            <>
              The code that you entered was not valid. Please double check your
              code and try again.
            </>
          </RedBanner>
        )}
        <ShadowBox>
          <div className="flex flex-col space-y-4">
            <p className="text-gray-500 dark:text-gray-400">
              To join Polar, enter your invite code
            </p>
            <Input
              name="polar-code"
              id="polar-code"
              placeholder="Your invite code"
              onUpdated={props.onInviteCodeUpdated}
            />

            <Checkbox
              id="accept_tos"
              value={props.acceptedTerms}
              onChange={props.onChangeAcceptedTerms}
            >
              I accept the{' '}
              <Link href="https://polar.sh/legal/terms" className="underline">
                Terms of Service
              </Link>{' '}
              and{' '}
              <Link href="https://polar.sh/legal/privacy" className="underline">
                Privacy Policy
              </Link>
            </Checkbox>

            <PrimaryButton
              disabled={props.joinDisabled}
              loading={props.joinLoading}
              onClick={props.onContinueClick}
            >
              Join
            </PrimaryButton>
          </div>
        </ShadowBox>
      </>
    </TakeoverBox>
  )
}
