'use client'

import React from 'react'
import { Modal } from '@/components/ui/modal'
import { Button } from '@/components/ui/button'
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'

interface DeleteTranscriptConfirmDialogProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  isDeleting?: boolean
}

export function DeleteTranscriptConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  isDeleting = false,
}: DeleteTranscriptConfirmDialogProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
        <div className="sm:flex sm:items-start">
          <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 dark:bg-red-900/20 sm:mx-0 sm:h-10 sm:w-10">
            <ExclamationTriangleIcon className="h-6 w-6 text-red-600 dark:text-red-400" aria-hidden="true" />
          </div>
          <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left flex-1">
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-gray-100">
              刪除逐字稿
            </h3>
            <div className="mt-4 space-y-3">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                確定要刪除此逐字稿嗎？此操作無法復原。
              </p>

              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-3">
                <h4 className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-2">
                  🔒 隱私保護
                </h4>
                <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
                  <li>✓ 逐字稿內容將被永久刪除</li>
                  <li>✓ 教練 session 記錄會保留</li>
                  <li>✓ 時數統計資料會保留</li>
                  <li>✓ 客戶資料會保留</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="bg-gray-50 dark:bg-gray-900 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse gap-3">
        <Button
          variant="danger"
          onClick={onConfirm}
          disabled={isDeleting}
          className="w-full sm:w-auto"
        >
          {isDeleting ? '刪除中...' : '確認刪除'}
        </Button>
        <Button
          variant="outline"
          onClick={onClose}
          disabled={isDeleting}
          className="mt-3 w-full sm:mt-0 sm:w-auto"
        >
          取消
        </Button>
      </div>
    </Modal>
  )
}
