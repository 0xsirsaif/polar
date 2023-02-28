import IssuePullRequest from "./IssuePullRequest"

const IssueReward = () => {
    return (<>
        <div className="bg-white shadow-xl rounded-xl p-4 mb-8 flex flex-col gap-2">
            <div className="flex items-center justify-between ">
                <div className="flex gap-2 items-center">
                    <span className="space-x-1 rounded-xl bg-[#FFE794] text-[#574814] px-1.5 py-0.5">
                        <span className="text-md">🏆</span>
                        <span className="text-sm font-medium">$700</span>
                    </span>
                    <span className="text-gray-500 text-sm">contributed by <span className="text-purple-500">Google</span></span>
                </div>
                <a href="#" className="text-gray-500 text-sm">Reward Details &rsaquo;</a>
            </div>


            <IssuePullRequest pullRequestState="open" issueState="open" />
            <IssuePullRequest pullRequestState="merged" issueState="closed" />

        </div>
    </>
    )
}

export default IssueReward