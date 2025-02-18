import Link from 'next/link'
import { useRouter } from 'next/router'
import { classNames } from 'polarkit/utils'

const BackerNavigation = () => {
  const router = useRouter()

  // All routes and conditions
  const navs = [
    {
      id: 'active-issues',
      title: 'Active Issues',
      link: `/feed`,
    },
    {
      id: 'rewards',
      title: 'Rewards',
      link: `/rewards`,
    },
  ]

  // Filter routes, set isActive, and if subs should be expanded
  const filteredNavs = navs.map((n) => {
    const isActive = router.asPath.startsWith(n.link)
    return {
      ...n,
      isActive,
    }
  })

  return (
    <div className="flex flex-row items-center justify-center gap-8 text-sm">
      {filteredNavs.map((n) => (
        <>
          <Link
            className={classNames(
              'hover:text-blue-700 dark:hover:text-blue-800',
              n.isActive ? 'text-blue-600' : 'text-gray-600 dark:text-gray-400',
            )}
            key={n.title}
            href={n.link}
          >
            <span className="font-medium ">{n.title}</span>
          </Link>
        </>
      ))}
    </div>
  )
}

export default BackerNavigation
