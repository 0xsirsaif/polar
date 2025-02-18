import React, { FunctionComponent, MouseEvent, useEffect } from 'react'
import ReactDOM from 'react-dom'
import FocusLock from 'react-focus-lock'

export interface ModalProps {
  isShown: boolean
  hide: () => void
  modalContent: JSX.Element
}

export const Modal: FunctionComponent<ModalProps> = ({
  isShown,
  hide,
  modalContent,
}) => {
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.keyCode === 27 && isShown) {
        hide()
      }
    }

    isShown
      ? (document.body.style.overflow = 'hidden')
      : (document.body.style.overflow = 'unset')

    document.addEventListener('keydown', onKeyDown, false)
    return () => {
      document.removeEventListener('keydown', onKeyDown, false)
    }
  }, [isShown, hide])

  const onInnerClick = (e: MouseEvent) => {
    // alert('inner')
    e.stopPropagation()
  }

  const modal = (
    <React.Fragment>
      <FocusLock>
        <div
          className="fixed top-0 bottom-0 left-0 right-0 z-50"
          aria-modal
          tabIndex={-1}
          role="dialog"
          onClick={(e) => {
            // alert('outer')
          }}
        >
          <div
            className="flex h-full w-full items-center justify-center bg-red-800/50"
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              // alert('modal mid')
              hide()
            }}
          >
            <div
              className="z-10 min-w-[800px] overflow-hidden rounded-xl bg-white shadow dark:bg-gray-800"
              onClick={onInnerClick}
            >
              {modalContent}
            </div>
          </div>
        </div>
      </FocusLock>
    </React.Fragment>
  )

  return isShown ? ReactDOM.createPortal(modal, document.body) : null
}

export const ModalHeader = (props: {
  children: React.ReactElement
  hide: () => void
}) => {
  return (
    <div className="flex w-full items-center justify-between border-b px-5 py-3 dark:bg-gray-800">
      <div>{props.children}</div>
      <button
        className="text-black hover:text-gray-800 dark:text-gray-100 dark:hover:text-gray-300"
        onClick={() => props.hide()}
      >
        <XIcon />
      </button>
    </div>
  )
}

const XIcon = () => {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M6 18L18 6M6 6L18 18"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
