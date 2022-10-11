#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
file: manager.py
description: 对照片进行管理，按规则删除照片，清理磁盘空间
             用法：
             python3 manager.py <start_date> <end_date>
             其中 start_date / end_date 为 8 位日期，如：
             python3 manager.py 20130101 20140331
author: 张翼
date: 2019-01-04 18:50:00
"""

import os
import sys
import shutil

ROOT_DIR = "/Users/zhangyi/Documents/Pictures"


def string_display_len(string):
    """ 获取一个字符串（含中英文、数字和符号）的“显示长度”，其中每个中文字符按 2 倍宽度算 """
    ascii_char_count = 0
    chinese_char_count = 0
    for char in string:
        if 0 <= ord(char) <= 127:
            ascii_char_count += 1
        else:
            chinese_char_count += 1
    return int(ascii_char_count + chinese_char_count * 2)


def size_info(size):
    """ 图片大小转换成显示的文字 """
    if size < 1024:
        return f"{size:.2f}B"
    size /= 1024
    if size < 1024:
        return f"{size:.2f}KB"
    size /= 1024
    if size < 1024:
        return f"{size:.2f}MB"
    size /= 1024
    return f"{size:.2f}GB"


def image_name(pic_file_name):
    """ 由于 NEF 在 LightRoom 修图后保存为 JPG 格式，且有 HDR 等可能的后缀因此
        因此，在判断一个 NEF 是否在 LightRoom / LightRoomMac 文件夹里有对应的版本，需要做一个转换
    """
    return pic_file_name[:
                         8]  # 可以同时覆盖 "IMG_XXXX.YYY" 和 "DSC_XXXX[-HDR].ZZZ" 这两类图片文件名


def dir_date(dir_name):
    """ 从目录中提取日期 """
    return dir_name[:8]


class DirectoryCleanupInfo:
    """
    一个目录经扫描后的清理信息
    """

    MIN_RESERVE_CNT = 5
    MIN_DELETE_CNT = 20

    def __init__(self, dir_name, total_file_cnt, delete_files):
        self.dir_name = dir_name
        self.total_file_cnt = total_file_cnt
        self.delete_files = delete_files
        self.delete_size = sum(
            [os.path.getsize(dir_name + os.sep + f) for f in delete_files])

    def delete_cnt(self):
        """ 删除图片数 """
        return len(self.delete_files)

    def reserve_cnt(self):
        """ 保留图片数 """
        return self.total_file_cnt - self.delete_cnt()

    def delete_size_info(self):
        """ 删除的空间大小（文本显示）"""
        return size_info(self.delete_size)

    def valid(self):
        """ 是否合法（真的需要删除）"""
        return self.reserve_cnt(
        ) >= DirectoryCleanupInfo.MIN_RESERVE_CNT and self.delete_cnt(
        ) >= DirectoryCleanupInfo.MIN_DELETE_CNT

    def get_info(self, dir_len, image_len, reserve_image_len, delete_image_len,
                 size_len):
        """ 信息 """
        gap_len = dir_len - string_display_len(self.dir_name)
        return f"目录名：{self.dir_name[len(ROOT_DIR)+len(os.sep):] + ' ' * gap_len} " \
            f"| 总图片数：{str(self.total_file_cnt).rjust(image_len)} " \
            f"| 保留图片数：{str(self.reserve_cnt()).rjust(reserve_image_len)} " \
            f"| 删除图片数：{str(self.delete_cnt()).rjust(delete_image_len)} " \
            f"| 节约空间：{self.delete_size_info().rjust(size_len)}"


class CleanupInfo:
    """
    所有需要清理的信息
    """

    PIC_EXT = set(["jpg", "nef"])
    DIR_EXT = set(["lightroom", "lightroommac"])
    PS_SUB_DIR = "selected"
    # SKIP_PATTERNS = []
    SKIP_PATTERNS = ["新西兰圆梦", "冰岛追梦", "东戴河", "三亚", "新加坡"]

    def __init__(self, start_date, end_date):
        self.infos = []
        self.skipped = []
        for d in os.listdir(ROOT_DIR):
            if any([d.find(p) >= 0 for p in CleanupInfo.SKIP_PATTERNS]):
                self.skipped.append(d)
                continue
            if dir_date(d) >= start_date and dir_date(d) <= end_date:
                info = self._gen_directory_cleanup_info(ROOT_DIR + os.sep + d)
                if info.valid():
                    self.infos.append(info)
        self.skipped.sort()
        self.infos.sort(key=lambda info: info.dir_name)

    def _gen_directory_cleanup_info(self, dir_name):
        sub_dir = dir_name + os.sep + CleanupInfo.PS_SUB_DIR
        return self._gen_directory_cleanup_info_ps(
            dir_name, sub_dir) if os.path.isdir(
                sub_dir) else self._gen_directory_cleanup_info_lr(dir_name)

    def _gen_directory_cleanup_info_ps(self, dir_name, sub_dir):
        """
        清理一个目录 - PS 子目录
        清理逻辑：如果在目录下有 selected 目录，则删除所有没有被 selected 选择的照片（认为是经挑选后的废片），只保留 selected 目录中的
        """
        all_pics = []
        delete_files = []
        for item in os.listdir(dir_name):
            full_path = dir_name + os.sep + item
            if item[-3:].lower() in CleanupInfo.PIC_EXT and os.path.isfile(
                    full_path):
                all_pics.append(item)
                delete_files.append(item)
        for sub_item in os.listdir(sub_dir):
            if sub_item[-3:].lower() in CleanupInfo.PIC_EXT and os.path.isfile(
                    sub_dir + os.sep + sub_item):
                all_pics.append(sub_item)
        return DirectoryCleanupInfo(dir_name, len(all_pics), delete_files)

    def _gen_directory_cleanup_info_lr(self, dir_name):
        """
        清理一个目录 - LR 子目录
        清理逻辑：如果在目录下有 LightRoom 修图过的目录，则删除所有没有被修图的照片（认为是经挑选后的废片），只保留之前在移动硬盘中的备份
        注意：德奥、新西兰行的照片有一些是之前用 JPEG 修图，现在只存了 NEF 之后没有完全修的，这些需要跳过并保留
        所以这个函数返回的信息一开始应该用于展示，经人肉确定后再删除
        """
        all_pics = []
        selected_pics = set()
        for item in os.listdir(dir_name):
            full_path = dir_name + os.sep + item
            if item[-3:].lower() in CleanupInfo.PIC_EXT and os.path.isfile(
                    full_path):
                all_pics.append(item)
            if item.lower() in CleanupInfo.DIR_EXT and os.path.isdir(
                    full_path):
                for sub_item in os.listdir(full_path):
                    if sub_item[-3:].lower(
                    ) in CleanupInfo.PIC_EXT and os.path.isfile(full_path
                                                                + os.sep
                                                                + sub_item):
                        selected_pics.add(image_name(sub_item))
        delete_files = [
            f for f in all_pics
            if len(selected_pics) > 0 and image_name(f) not in selected_pics
        ]
        return DirectoryCleanupInfo(dir_name, len(all_pics), delete_files)

    def __str__(self):
        max_dir_len = 0
        max_total_cnt = 0
        max_reserve_cnt = 0
        max_delete_cnt = 0
        max_size_len = 0
        for info in self.infos:
            max_dir_len = max(max_dir_len, string_display_len(info.dir_name))
            max_total_cnt = max(max_total_cnt, info.total_file_cnt)
            max_reserve_cnt = max(max_reserve_cnt, info.reserve_cnt())
            max_delete_cnt = max(max_delete_cnt, info.delete_cnt())
            max_size_len = max(max_size_len, len(info.delete_size_info()))
        result = "\n".join([
            info.get_info(max_dir_len, len(str(max_total_cnt)),
                          len(str(max_reserve_cnt)), len(str(max_delete_cnt)),
                          max_size_len) for info in self.infos
        ])
        result += f"\n总节约空间：{size_info(sum([info.delete_size for info in self.infos]))}\n跳过目录：\n"
        result += "\n".join(self.skipped)
        return result

    def clear(self):
        """
        进行真正的清理
        """
        print("开始清理")
        n = len(self.infos)
        for i, dir_info in enumerate(self.infos):
            print(
                f"[{i+1:03d}/{n:03d}] 清理目录 [{len(dir_info.delete_files):03d} files] -> {dir_info.dir_name}"
            )
            for item in dir_info.delete_files:
                try:
                    os.remove(dir_info.dir_name + os.sep + item)
                except Exception as ex:
                    print(f"  删除文件 '{item}' 发生错误：{ex}")
            shutil.move(dir_info.dir_name, dir_info.dir_name + "_(incomplete)")


def _valid_date(date):
    return len(date) == 8 and date.isdigit()


def main():
    """ main program """
    if len(sys.argv) <= 2:
        print(
            f"用法：\npython3 {os.path.basename(sys.argv[0])} <start_date> <end_date>"
        )
        sys.exit(-1)
    start = sys.argv[1]
    end = sys.argv[2]
    if not _valid_date(start) or not _valid_date(end):
        print("日期非法，应该为 8 位数字，格式为 'yyyymmdd'")
        sys.exit(-1)
    infos = CleanupInfo(start, end)
    print(infos)
    infos.clear()


if __name__ == "__main__":
    main()
